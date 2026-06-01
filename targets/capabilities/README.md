# Target Capability Contracts

`target-capabilities.json` is the tracked capability contract for the current
Python adapters.

It records, per target:

- exposed output surfaces
- claimed support level for each current SDJ/VSS scene feature
- notes about lossiness and omissions

Runtime code in `src/vss/capabilities.py` loads this file directly. When target
support changes, update the contract and the adapter behavior together.
