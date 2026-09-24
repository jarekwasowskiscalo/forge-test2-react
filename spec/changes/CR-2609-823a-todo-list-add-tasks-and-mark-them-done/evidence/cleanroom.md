# From-scratch evidence -- CR-2609-823a

*Recorded with the `add-evidence` verb from .sdd/reports/cleanroom.json. It renders the same as printed for the run -- one format, one producer.*

```
VERDICT GREEN (from scratch, 4 steps)
  [ok] setup         3.9s  a dependency that is in somebody's virtualenv and in no mani
  [ok] migrate       9.2s  a migration chain that cannot run from an empty database
  [ok] generate      4.9s  a committed contract whose generator no longer reproduces it
  [ok] check       298.5s  everything CI runs, against a tree nobody has warmed up
  WARNING: 1 files are uncommitted. A cold run clones HEAD,
         so those changes are NOT proved by it -- commit and repeat.
```
