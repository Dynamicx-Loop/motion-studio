# Bundled assets

This directory holds portable, versioned assets shipped with Motion Studio.
`robots/astro_p2/` contains the built-in default Astro P2 model and its meshes,
source notices, SHA-256 manifest and owned Studio import derivative.

`menagerie_x` remains the source of Astro changes. Updates are explicit snapshots
of a reviewed source revision; importing or viewing the built-in uses this local
copy and never fetches or modifies another repository. New managed assets and
generated results still belong to the selected Studio state or `outputs/`.

See the [Astro snapshot](robots/astro_p2/README.md) for provenance, licenses,
the update command and validation scope. Historical definitions under `robots/`
retain their original pins and are separate from this current application asset.
