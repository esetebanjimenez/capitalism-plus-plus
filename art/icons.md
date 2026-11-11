# Job icons (M2, B+)

16 job icons at 48 px, one per job type, are drawn in code by `tools/icons.py` with a 1 px ink outline.
They use the shared 48-colour palette, are original art and are drawn pixel by pixel.
Rebuild them with `python3 art/tools/icons_build.py`.

- Files: `tiles/icons/job_<name>.png`. Atlas: `atlas/icons_atlas.png` + `.json` (48 px grid, transparent).
- Names: crop_growing, livestock_raising, livestock_processing, logging, inventory, private_labelling,
  manufacturing, mining, oil_extraction, purchasing, research_development, sales, software_development,
  software_production, advertising, import.
- Show them at 1x (or 2x on large screens) with nearest-neighbour scaling, in the 3×3 slot grid on the cream panel.
