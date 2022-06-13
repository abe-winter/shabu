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

    def build(self, name, outer, db, args) -> int:
        "compute tag + run docker build, write to shadb. returns shadb rowid (to use for push)"
        clean = gitapi.clean()
        sha = gitapi.sha()
        existing = list(shadb.existing(db, name, sha))
        suffix = ''
        build_num = max([row['build_count'] for row in existing]) + 1 if existing else 0
        if existing and clean:
            logger.warning('[%s] existing clean build. not setting build number on tag', name)
        elif existing and not clean:
            suffix = f'.b{build_num}'
        else:
            logger.debug('[%s] no existing builds in db', name)
        short = sha[:outer.short]
        registry = self.registry or outer.registry
        base_tag = '/'.join(filter(None, (registry, name)))
        tag = f"{base_tag}:{short}{suffix}"
        logger.debug('[%s] tag is %s', name, tag)
        # todo: find docs for last arg being workdir
        ret = subprocess.run(f"docker build -f {self.workdir}/{self.dockerfile} -t {tag} {self.workdir}", shell=True, capture_output=args.quiet)
        ret.check_returncode()
        rowid = shadb.writebuild(db, name, sha, short, not clean, build_num)
        db.commit()
        return rowid

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
    p.add_argument('-e', '--dotenv', help="path to shas env file (used by other )", default='shas.env')
    p.add_argument('-l', '--level', help="log level", default='info')
    p.add_argument('--only', help="only build one named build") # todo: nargs=*
    p.add_argument('-p', '--push', help="push as well as build", action='store_true')
    p.add_argument('-q', '--quiet', help="capture docker shell output", action='store_true')
    args = p.parse_args()

    logging.basicConfig(level=getattr(logging, args.level.upper()))

    db = shadb.migrate_db(args)
    conf = Conf.parse(args)
    logger.debug('parsed conf with %d builds', len(conf.builds))
    envfile = Envfile.parse(args.dotenv)
    logger.debug('existing env %s', envfile.lookup())
    for name, build in conf.builds.items():
        rowid = build.build(name, conf, db, args)
        logger.debug('[%s] rowid %d', name, rowid)
        if args.push:
            raise NotImplementedError('todo: push')
            # envfile[] = ...
    envfile.write(args.dotenv)
    logger.debug('wrote dotenv')
