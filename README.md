# shabu

'sha build'

Build, version tagging + push manager for docker.

Git-aware and increments build suffix for dirty local builds.

Versions are stored locally for now so you can't easily share this with a team.

## mini docs

```
# install
pip install git+https://github.com/abe-winter/shabu.git

# create a config file
# look at shabu.json in this repo

# CLI docs
shabu -h

# build without pushing
shabu

# build with push
shabu -p
```

## similar tools to investigate

- bazel's [docker rules](https://github.com/bazelbuild/rules_docker)
- skaffold

## todo

- [ ] try https://github.com/mtkennerly/dunamai version strings or https://pypi.org/project/incremental
