The Interlock TOR website follows a standard format to view/access files. The scripts in this repo can be used to obtain statistics on common filetypes that have been exfiltrated as well as obtain copies of files of interest from the leak.

# Usage

## Tree Parser

The parser is designed to generate stats on common file types, therefore it is recommended to always run with the **--files-only** argument unless you have a specific need for formatted directory structure in the output.

### With tqdm (automatic if installed)
```python
python interlock_tree_parser.py tree.txt --files-only -o results.txt
```

### Force simple progress (no tqdm)
```python
python interlock_tree_parser.py tree.txt --files-only --no-tqdm -o results.txt
```

### Custom progress interval for fallback mode

```python
python interlock_tree_parser.py tree.txt --progress-interval 25000 -o results.txt
```