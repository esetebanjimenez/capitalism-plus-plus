# Manufacturing Recipes

Extracted from `1STD.SET` METHOD resource (standard game set).
54 recipes define how products are manufactured in factories.

## How recipes work

Each recipe specifies:
- **Output**: the product manufactured, and how many units per production cycle
- **Inputs**: 1–5 ingredient products, each with a required quantity and a
  quality weight (the % contribution of that ingredient's quality to the output's
  overall quality — the remaining weight comes from manufacturing skill)
- **Production speed**: base time multiplier (100 = normal, 200 = double time,
  300 = triple, 400 = quadruple)

A manufacturing job in a factory links to purchasing jobs that supply its
ingredients. The recipe determines which products must be on hand and in what
proportions. Quality weights sum to less than 100; the remainder is the
factory's own manufacturing skill contribution to output quality.

## R&D prerequisites

Some products require researching another product first (stored in ITEMPAE).
These are R&D dependencies, not manufacturing inputs:

| Product | Requires first |
|---------|---------------|
| DVD Player             | Desktop Computer |
| Desktop Computer       | Television |
| Internet-TV            | Desktop Computer |
| PDA                    | Desktop Computer |
| VR Computer            | Desktop Computer |
| Video Camera           | Camera + Television |
| Video Recorder         | Television |
| Wrist Computer         | Desktop Computer |

---

## All recipes by product class

### Semi-products

**Textiles** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Cotton                   |    1 |  50% |
| *Manufacturing skill*    |      |  50% |

**Wheel & Tire** (1 units)  (speed: 200%)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Rubber                   |   20 |  25% |
| Steel                    |   20 |  25% |
| *Manufacturing skill*    |      |  50% |

**Flour** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Wheat                    |    1 |  70% |
| *Manufacturing skill*    |      |  30% |

**Electronic Components** (3 units)  (speed: 400%)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Chemical Minerals        |    1 |  10% |
| Silicon                  |    1 |  10% |
| Steel                    |    1 |  10% |
| *Manufacturing skill*    |      |  70% |

**Steel** (2 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Coal                     |    1 |  20% |
| Iron Ore                 |    1 |  30% |
| *Manufacturing skill*    |      |  50% |

**Plastic** (30 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Oil                      |    1 |  35% |
| *Manufacturing skill*    |      |  65% |

**Silicon** (2 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Silica                   |    2 |  40% |
| *Manufacturing skill*    |      |  60% |

**Glass** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Silica                   |    1 |  40% |
| *Manufacturing skill*    |      |  60% |

**Paper** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Timber                   |    1 |  50% |
| *Manufacturing skill*    |      |  50% |

**Car Body** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Glass                    |   30 |  15% |
| Plastic                  |   30 |  15% |
| Steel                    |  600 |  20% |
| *Manufacturing skill*    |      |  50% |

**CPU** (100 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Silicon                  |    1 |   5% |
| *Manufacturing skill*    |      |  95% |

**Engine** (1 units)  (speed: 200%)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Steel                    |  100 |  20% |
| *Manufacturing skill*    |      |  80% |

### Automobile

**Car** (1 units)  (speed: 300%)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Car Body                 |    1 |  30% |
| Engine                   |    1 |  30% |
| Wheel & Tire             |    4 |  10% |
| *Manufacturing skill*    |      |  30% |

**Motorcycle** (1 units)  (speed: 200%)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Engine                   |    1 |  30% |
| Steel                    |   10 |  10% |
| Wheel & Tire             |    2 |  10% |
| *Manufacturing skill*    |      |  50% |

### Beverage

**Bottled Milk** (8 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Milk                     |    2 |  65% |
| Glass                    |    1 |   5% |
| *Manufacturing skill*    |      |  30% |

**Beer** (17 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Barley                   |    5 |  40% |
| Aluminum                 |    1 |   5% |
| *Manufacturing skill*    |      |  55% |

**Wine** (6 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Grapes                   |    5 |  50% |
| Glass                    |    1 |   5% |
| *Manufacturing skill*    |      |  45% |

**Cola** (17 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Sugar                    |    5 |  10% |
| Aluminum                 |    1 |  10% |
| *Manufacturing skill*    |      |  80% |

### Chemical Products

**Diaper** (6 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Cotton                   |    1 |  15% |
| Paper                    |    1 |  15% |
| *Manufacturing skill*    |      |  70% |

**Toothpaste** (20 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Chemical Minerals        |    3 |  25% |
| Plastic                  |    1 |   5% |
| *Manufacturing skill*    |      |  70% |

**Shampoo** (15 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Chemical Minerals        |    3 |  25% |
| Plastic                  |    1 |   5% |
| *Manufacturing skill*    |      |  70% |

**Detergent** (10 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Chemical Minerals        |    3 |  25% |
| Plastic                  |    1 |   5% |
| *Manufacturing skill*    |      |  70% |

### Cigarette

**Cigarettes** (50 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Tobacco                  |    1 |  40% |
| Paper                    |    1 |  10% |
| *Manufacturing skill*    |      |  50% |

### Computer

**PDA** (5 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| CPU                      |    5 |  20% |
| Electronic Components    |    1 |  20% |
| Plastic                  |    2 |   0% |
| *Manufacturing skill*    |      |  60% |

**Wrist Computer** (2 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| CPU                      |    2 |  40% |
| Electronic Components    |    2 |  15% |
| Plastic                  |    1 |   5% |
| *Manufacturing skill*    |      |  40% |

**Desktop Computer** (1 units)  (speed: 200%)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| CPU                      |    1 |  40% |
| Electronic Components    |    1 |  15% |
| Steel                    |    1 |   5% |
| *Manufacturing skill*    |      |  40% |

**VR Computer** (2 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| CPU                      |    1 |  30% |
| Glass                    |    2 |  10% |
| *Manufacturing skill*    |      |  60% |

**Internet-TV** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| CPU                      |    1 |  35% |
| Glass                    |    2 |   5% |
| Plastic                  |    2 |   5% |
| *Manufacturing skill*    |      |  55% |

### Cosmetics

**Perfume** (10 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Chemical Minerals        |    1 |  25% |
| Glass                    |    1 |   5% |
| *Manufacturing skill*    |      |  70% |

**Eye Shadow** (10 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Chemical Minerals        |    1 |  25% |
| Plastic                  |    1 |   5% |
| *Manufacturing skill*    |      |  70% |

### Electronic Products

**DVD Player** (2 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| CPU                      |    2 |  30% |
| Electronic Components    |    1 |  15% |
| Plastic                  |    1 |   5% |
| *Manufacturing skill*    |      |  50% |

**Television** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Electronic Components    |    3 |  20% |
| Glass                    |    2 |   5% |
| Plastic                  |    2 |   5% |
| *Manufacturing skill*    |      |  70% |

**Camera** (6 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Electronic Components    |    1 |  20% |
| Glass                    |    1 |   5% |
| Plastic                  |    1 |   5% |
| *Manufacturing skill*    |      |  70% |

**Video Camera** (6 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Electronic Components    |    1 |  20% |
| Glass                    |    1 |   5% |
| Plastic                  |    1 |   5% |
| *Manufacturing skill*    |      |  70% |

**Video Recorder** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Electronic Components    |    1 |  20% |
| Plastic                  |    1 |   5% |
| Steel                    |    1 |   5% |
| *Manufacturing skill*    |      |  70% |

**Hi-fi** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Electronic Components    |    2 |  20% |
| Plastic                  |    3 |   5% |
| Steel                    |    3 |   5% |
| *Manufacturing skill*    |      |  70% |

**Air Conditioner** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Electronic Components    |    1 |  20% |
| Plastic                  |    3 |   5% |
| Steel                    |    6 |   5% |
| *Manufacturing skill*    |      |  70% |

### Food

**Chocolate Bar** (10 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Milk                     |    1 |  20% |
| Cocoa                    |    1 |  30% |
| *Manufacturing skill*    |      |  50% |

**Ice Cream** (30 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Milk                     |    2 |  30% |
| Sugar                    |    1 |  10% |
| *Manufacturing skill*    |      |  60% |

**Cookies** (10 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Sugar                    |    1 |  30% |
| Flour                    |    9 |  10% |
| *Manufacturing skill*    |      |  60% |

**Bread** (10 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Flour                    |    9 |  40% |
| *Manufacturing skill*    |      |  60% |

### Furniture

**Sofa** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Leather                  |    5 |  30% |
| Cotton                   |    5 |  10% |
| Timber                   |   30 |  20% |
| *Manufacturing skill*    |      |  40% |

**Bed** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Timber                   |  100 |  50% |
| *Manufacturing skill*    |      |  50% |

### Jewelry

**Jewelry** (1 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Gold                     |    1 |  70% |
| *Manufacturing skill*    |      |  30% |

### Toy

**Toy Bear** (15 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Cotton                   |    2 |  10% |
| Textiles                 |    1 |  30% |
| *Manufacturing skill*    |      |  60% |

**Toy Train** (4 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Plastic                  |    1 |  10% |
| Steel                    |    1 |  10% |
| *Manufacturing skill*    |      |  80% |

### Watch

**Watch** (50 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Glass                    |    1 |  10% |
| Steel                    |    1 |  10% |
| *Manufacturing skill*    |      |  80% |

### Apparel, Footwear & Bags

**Sport Shoes** (6 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Leather                  |    1 |  30% |
| Cotton                   |    1 |   5% |
| Rubber                   |    1 |   5% |
| *Manufacturing skill*    |      |  60% |

**Leather Shoes** (6 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Leather                  |    2 |  45% |
| Rubber                   |    1 |   5% |
| *Manufacturing skill*    |      |  50% |

**Leather Jacket** (6 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Leather                  |    5 |  45% |
| Textiles                 |    1 |   5% |
| *Manufacturing skill*    |      |  50% |

**Leather Briefcase** (6 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Leather                  |    5 |  45% |
| Textiles                 |    1 |   5% |
| *Manufacturing skill*    |      |  50% |

**Sweater** (2 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Wool                     |    1 |  50% |
| *Manufacturing skill*    |      |  50% |

**Socks** (20 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Wool                     |    1 |  60% |
| *Manufacturing skill*    |      |  40% |

**Jeans** (2 units)

| Input | Qty | Quality weight |
|-------|----:|---------------:|
| Textiles                 |    1 |  50% |
| *Manufacturing skill*    |      |  50% |

---

## Supply chain overview

### Raw material processing (mine/oil well/logging camp → factory)

| Raw material | Produces | Via recipe |
|-------------|----------|-----------|
| Gold                 | Jewelry              | 1:1 ratio |
| Oil                  | Plastic              | 1:30 ratio |
| Silica               | Silicon              | 2:2 ratio |
| Silica               | Glass                | 1:1 ratio |
| Timber               | Bed                  | 100:1 ratio |
| Timber               | Paper                | 1:1 ratio |
| Coal + Iron Ore      | Steel                | 1 + 1 |

### Plant processing (farm → factory)

| Plant product | Produces | Via recipe |
|--------------|----------|-----------|
| Cotton               | Textiles             | 1:1 ratio |
| Wheat                | Flour                | 1:1 ratio |

### Complete supply chains

**Car**: Iron Ore + Coal → Steel; Silica → Glass; Oil → Plastic;
  Rubber + Steel → Wheel & Tire; Steel → Engine;
  Glass + Plastic + Steel → Car Body;
  Car Body + Engine + 4× Wheel → Car

**Desktop Computer**: Chemical + Silicon + Steel → Electronic Components;
  Silicon → CPU; CPU + Electronic Components + Steel → Desktop Computer

**Motorcycle**: Steel → Engine; Rubber + Steel → Wheel;
  Engine + Steel + 2× Wheel → Motorcycle
