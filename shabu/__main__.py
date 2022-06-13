import argparse, json, sqlite3, logging, subprocess
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BuildConf:
    registry: Optional[str]
    dockerfile: Optional[str] = 'Dockerfile'
    workdir: str = '.'

    def run(self, outer, _args):
        registry = self.registry or outer.registry
        version = 
        subprocess.run('docker build -t ', shell=True)

@dataclass
class Conf:
    builds: Dict[str, BuildConf] # {name: conf}. name used for tag
    registry: Optional[str] # global
    short: int = 8 # short sha length

    @classmethod
    def parse(cls, args):
        with open(args.conf, encoding='utf8') as f:
            raw = json.load(f)
        return Cls(**raw)

def git_is_clean():
    raise NotImplementedError

MIGRATIONS = [
    (1, 'initial', ['create table if not exists builds (id integer primary key autoincrement, full_sha text, short_sha text, dirty bool, build_suffix text, created text)']),
]

def migrate_db(args):
    "return opened, migrated DB"
    db = sqlite3.connect(args.db)
    with db:
        db.execute('create table if not exists migrations (id integer primary key, label text, created text)');
        max_id, = db.execute('select max(id) from migrations').fetchone()
        max_id = max_id or 0
        logging.debug('max id %s', max_id)
        for index, label, stmts in MIGRATIONS:
            if max_id >= index:
                continue
            for stmt in stmts:
                db.execute(stmt)
            db.execute('insert into migrations (id, label, created) values (?, ?, ?)', (index, label, datetime.utcnow().isoformat()))
            logger.debug('ok migration %d %s with %d stmts', index, label, len(stmts))
    return db

def main():
    p = argparse.ArgumentParser(description="docker build version + push manager")
    p.add_argument('--conf', help="path to conf json", default='shabu.json')
    p.add_argument('--db', help="path to history db", default='shabu.sqlite')
    p.add_argument('--level', help="log level", default='info')
    args = p.parse_args()

    logging.basicConfig(level=getattr(logging, args.level.upper()))

    db = migrate_db(args)
    conf = Conf.parse(args)
    print('conf', conf)
    raise NotImplementedError
