# PKU-Market-PCB Dataset

## Download

1. Download the PKU-Market-PCB dataset from the original source or Kaggle
2. Extract the contents into this `data/` directory

Expected structure after extraction:

```
data/
├── Missing_hole/
│   ├── 01_missing_hole_01.jpg
│   ├── 01_missing_hole_01.xml
│   └── ...
├── Mouse_bite/
│   ├── 01_mouse_bite_01.jpg
│   ├── 01_mouse_bite_01.xml
│   └── ...
├── Open_circuit/
├── Short/
├── Spur/
└── Spurious_copper/
```

Each defect type folder contains:
- `.jpg` images of PCBs with that defect type
- `.xml` annotation files in Pascal VOC format with bounding box coordinates

## Defect Types

| Type | Description |
|------|-------------|
| Missing hole | Drill hole that should exist but is absent |
| Mouse bite | Irregular jagged edges on trace or copper area |
| Open circuit | Break or gap in a copper trace |
| Short | Unintended copper bridging between traces |
| Spur | Unwanted copper protrusion from a trace |
| Spurious copper | Extra copper residue not belonging to any circuit |
