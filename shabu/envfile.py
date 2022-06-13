import re, os, shutil

RE_KV = re.compile('^([\w-]+)=(.+)$')

class Envfile(list):
    "helper to parse and format envfiles (name=value lines), preserves ignore lines (comments for example)"

    @classmethod
    def parse(cls, path: str):
        "factory. takes file path"
        if not os.path.exists(path):
            return cls()
        with open(path, encoding='utf8') as f:
            return cls(line.strip() for line in f)

    def lookup(self):
        "return dict of {key, row}. error if dupes"
        ret = {}
        for i, line in enumerate(self):
            if (match := RE_KV.match(line)):
                key = match.groups()[0]
                if key in ret:
                    raise KeyError('dupe key', key)
                ret[key] = i
        return ret

    def __setitem__(self, key, val):
        if isinstance(key, int):
            return super().__setitem__(key, val)
        elif not isinstance(key, str):
            raise TypeError('expected str or int index', type(key))
        index = self.lookup().get(key)
        row = f'{key}={val}'
        if index is None:
            self.append(row)
        else:
            self[index] = row

    def write(self, path: str, backup: bool = True):
        "write to path, optionally copy existing to backup"
        if backup and os.path.exists(path):
            shutil.copy(path, path + '.backup')
        with open(path, 'w', encoding='utf8') as f:
            f.write('\n'.join(self))
            f.write('\n')
