# Design

## Stream-Interface

- init(stage: int, dt_s: float)
- push(array)
- flush()

### These classes are Stream-Sinks and implement the Stream-Interface

- class Density (in and out)
- class FIR
- class OutTrash

### These classes are Stream-Sources - tyeh drive a Stream-Interface

- class InThread
- class InSynthetic
- class InFile

### Example pipelines

- InSynthetic -> FIR -> Density -> FIR -> Density -> OutTrash
- Picosope -> InThread -> FIR -> Density -> FIR -> Density -> OutTrash
