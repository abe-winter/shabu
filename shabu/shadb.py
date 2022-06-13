"sqlite database for shas"
import sqlite3, logging
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)

MIGRATIONS = [
    (1, 'initial', ['create table if not exists builds (id integer primary key autoincrement, name text, full_sha text, short_sha text, dirty bool, build_count integer default 0, pushed bool default 0, created text default now)']),
]

def migrate_db(args) -> sqlite3.Connection:
    "return opened, migrated DB"
    db = sqlite3.connect(args.db)
    with db:
        db.execute('create table if not exists migrations (id integer primary key, label text, created text default now)');
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
    db.row_factory = sqlite3.Row
    return db

def existing(db: sqlite3.Connection, name: str, full_sha: str) -> List[sqlite3.Row]:
    "return list of rows for existing builds for this sha"
    return db.execute('select * from builds where name = ? and full_sha = ?', (name, full_sha))

def writebuild(db: sqlite3.Connection, name: str, full_sha: str, short: str, dirty: bool, build_num: int) -> id:
    "return integer id of build"
    ret = db.execute('insert into builds (name, full_sha, short_sha, dirty, build_count) values (?, ?, ?, ?, ?)', (name, full_sha, short, dirty, build_num))
    return ret.lastrowid

def get(db: sqlite3.Connection, rowid: int) -> sqlite3.Row:
    "get a build"
    return db.execute('select * from builds where id = ?', (rowid,)).fetchone()

def set_pushed(db: sqlite3.Connection, rowid: int) -> sqlite3.Cursor:
    return db.execute('update builds set pushed = 1 where rowid = ?', (rowid,))
