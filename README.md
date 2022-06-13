# shabu

'sha build'

Build, version tagging + push manager for docker.

Git-aware and increments build suffix for dirty local builds.

Versions are stored locally for now so you can't easily share this with a team.

## mini docs

```
# install
pip install https://github.com/abe-winter/shabu.git

# create a config file
# look at shabu.json in this repo

# CLI docs
shabu -h

# build without pushing
shabu

# build with push
shabu -p
```
