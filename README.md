# compas_grid

Model of simple grid structures for multi-storey buildings.

## Workflow

```mermaid
flowchart LR
    A{Geometry (Point, Lines, Explode Mesh Faces)} --> 
    B(Graph) --> 
    C(Cell Network) -->
    D(Model)

[```mermaid
---
config:
  layout: fixed
  look: neo
  theme: mc
---
flowchart TD
    A("fa:fa-cube Geometry:<br>Points, Lines, Faces<br>") --> B("fa:fa-diagram-project Graph<br>")
    B --> C["fa:fa-diagram-project CellNetwork"]
    C --> n4["fa:fa-diagram-project Model<br>"]
    C@{ shape: rounded}
    n4@{ shape: rounded}](url)


## Commit style

```bash
git commit -m "ADD <description>"         <--- for adding new elements
git commit -m "FIX <description>"         <--- for fixing (errors, typos)
git commit -m "FLASH <description>"       <--- quick checkpoint before refactoring
git commit -m "MILESTONE <description>"   <--- for capping moment in development
git commit -m "CAP <description>"         <--- for for less important milestones
git commit -m "UPDATE <description>"      <--- for moddification to the same file
git commit -m "MISC <description>"        <--- for any other reasons to be described
git commit -m "WIP <description>"         <--- for not finished work
git commit -m "REFACTOR <description>"    <--- for refactored code
git commit -m "MERGE <description>"       <--- for merging operations
git commit -m "WIP-CAP <description>"     <--- for when combining multiple commits into one
```

## Installation

Stable releases can be installed from PyPI.

```bash
pip install compas_grid
```

To install the latest version for development, do:

```bash
git clone https://github.com//compas_grid.git
cd compas_grid
pip install -e ".[dev]"
```

## Documentation

For further "getting started" instructions, a tutorial, examples, and an API reference,
please check out the online documentation here: [compas_grid docs](https://.github.io/compas_grid)

## Issue Tracker

If you find a bug or if you have a problem with running the code, please file an issue on the [Issue Tracker](https://github.com//compas_grid/issues).

