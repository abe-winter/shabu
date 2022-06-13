import argparse, json, logging, subprocess
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass
from .envfile import Envfile
from . import gitapi, shadb

logger = logging.getLogger(__name__)

@dataclass
class BuildConf:
    registry: Optional[str] = None
    dockerfile: Optional[str] = 'Dockerfile'
    workdir: str = '.'
    # todo: build args
    # todo: optional 'latest' ('always', 'clean', 'no')

    def tag(self, name, outer, row) -> str:
        "format a tag from a shadb row and other context"
        suffix = f'.b{row["build_count"]}' if row and row['dirty'] else ''
        registry = self.registry or outer.registry
        base_tag = '/'.join(filter(None, (registry, name)))
        return f"{base_tag}:{row['short_sha']}{suffix}"

    def build(self, name, outer, db, args) -> int:
        "compute tag + run docker build, write to shadb. returns shadb rowid (to use for push)"
        clean = gitapi.clean()
        sha = gitapi.sha()
        existing = list(shadb.existing(db, name, sha))
        build_num = max([row['build_count'] for row in existing]) + 1 if existing else 0
        rowid = shadb.writebuild(db, name, sha, sha[:outer.short], not clean, build_num)
        row = shadb.get(db, rowid)
        tag = self.tag(name, outer, row)
        logger.debug('[%s] tag is %s', name, tag)
        # todo: find docs for last arg being workdir
        subprocess.run(f"docker build -f {self.workdir}/{self.dockerfile} -t {tag} {self.workdir}", shell=True, capture_output=args.quiet) \
            .check_returncode()
        db.commit()
        return rowid

    def push(self, name, outer, db, args, rowid) -> str:
        "returns tag"
        row = shadb.get(db, rowid)
        assert row['name'] == name
        tag = self.tag(name, outer, row)
        logger.debug('pushing tag %s', tag)
        if row['pushed']:
            logger.warning('[%s] %s already pushed per db', name, tag)
        if not (self.registry or outer.registry):
            logger.warning('[%s] pushing without registry, guessing this will fail', name)
        shadb.set_pushed(db, rowid)
        subprocess.run(f'docker push {tag}', shell=True, capture_output=args.quiet) \
            .check_returncode()
        db.commit()
        return tag

@dataclass
class Conf:
    builds: Dict[str, BuildConf] # {name: conf}. name used for tag
    registry: Optional[str] = None # global
    short: int = 8 # short sha length

    @classmethod
    def parse(cls, args):
        with open(args.conf, encoding='utf8') as f:
            raw = json.load(f)
        ret = cls(**raw)
        ret.builds = {key: BuildConf(**val) for key, val in ret.builds.items()}
        return ret

def main():
    p = argparse.ArgumentParser(description="docker build version + push manager")
    p.add_argument('-c', '--conf', help="path to conf json", default='shabu.json')
    p.add_argument('--db', help="path to history db", default='shabu.sqlite')
    p.add_argument('-e', '--dotenv', help="path to tags env file (used by orchestration tools)", default='tags.env')
    p.add_argument('-l', '--level', help="log level", default='info')
    p.add_argument('--only', help="only build one named build") # todo: nargs=*
    p.add_argument('-p', '--push', help="push as well as build", action='store_true')
    p.add_argument('-q', '--quiet', help="capture docker shell output", action='store_true')
    p.add_argument('--last', help="don't build, use most recent build for push", action='store_true')
    args = p.parse_args()

    logging.basicConfig(level=getattr(logging, args.level.upper()))

    if args.only:
        raise NotImplementedError('--only not supported yet')
    if args.last:
        raise NotImplementedError('--last not supported yet')

    db = shadb.migrate_db(args)
    conf = Conf.parse(args)
    logger.debug('parsed conf with %d builds', len(conf.builds))
    envfile = Envfile.parse(args.dotenv)
    logger.debug('existing env %s', envfile.lookup())
    for name, build in conf.builds.items():
        rowid = build.build(name, conf, db, args)
        logger.debug('[%s] rowid %d', name, rowid)
        if args.push:
            tag = build.push(name, conf, db, args, rowid)
            _, version = tag.split(':')
            envfile[f'{name}_tag'] = tag
            envfile[f'{name}_version'] = version
    envfile.write(args.dotenv)
    logger.debug('wrote dotenv')
