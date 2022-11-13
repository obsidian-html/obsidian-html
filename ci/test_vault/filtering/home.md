This folder contains folder structures to test the note filtering that we can do with `exclude_subfolders` and `included_folders`.

# Test 1: simple inclusion
``` yaml
obsidian_entrypoint_path_str: 'ci/test_vault/filtering/home.md'
included_folders:
  - filtering
```

This should give us the following html output:

```
filtering/<full folder>
index.md
```

# Test 2: simple exclusion
``` yaml
obsidian_entrypoint_path_str: 'ci/test_vault/filtering/home.md'
included_folders:
  - filtering
exclude_subfolders:
  - "/filtering/excl
```

This should give us the following html output:

```
filtering/
  neutral/<full folder>
index.md
```



# Link notes
Link to all relevant notes, otherwise they will not be included anyways

- [[excluded]]
- [[neutral]]
- [[RossettiGoblinMarket.pdf]]
- 