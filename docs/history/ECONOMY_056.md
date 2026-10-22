# 0.5.6 economic pass — development source

This pass specializes the five starting economies without changing their people,
population classes, raw goods, terrain, borders or settlement ranks. It targets
the installed EU5 1.3.11 definitions. The bundled installer remains the released
0.5.5 package; these changes require a new build and a new campaign.

## National roles

| Crown | People including mixed populations | Building levels | Capital levels | Role |
| --- | ---: | ---: | ---: | --- |
| Cindermaw | 712,688 | 47 | 17 | Tools, weapons and secondary pottery; largest diversified base |
| Brackmaw | 391,818 | 36 | 13 | Grain, livestock, salt, cloth and naval provisioning |
| Shatterfin | 262,607 | 16 | 11 | Wharves, naval supplies, sailcloth and inter-island shipping |
| Reefhook | 130,392 | 12 | 6 | Fishing, pearls and harbor trade |
| Sootwake | 121,191 | 12 | 5 | Timber and charcoal with a small repair industry |

Hooktooth has three tools and three weapons guild levels. Brackhaven has three
naval-supplies guild levels, two cloth levels and three granaries. Shatterfin has
two wharf, naval-supplies and cloth levels each. Reefhook exchanges its generic
tools/cloth/pottery package for trade and boat supplies. Sootwake has two rural
charcoal makers in wooded districts; Cindermaw retains one for basic resilience.
Sootwake has the same total infrastructure as Reefhook, but a smaller capital.

Sootwake supplies fuel for Cindermaw's smiths. Brackmaw processes provisions and
naval supplies using island-market fiber and tar. Reefhook trades fish and pearls
for grain and manufactured goods. Shatterfin supports maritime work across its
two islands and depends on traded provisions. These are partial specializations,
not guaranteed autarky or scripted trade flows. The shared Hooktooth market is
retained; engine market membership and transport costs need observation in play.

## Geography and scale

Forestry stays in woods, smelting on metal deposits, farms on food/pastoral goods,
and charcoal in wooded districts. Larger farming and forestry communities receive
extra village levels; marginal small districts lose unnecessary market villages.
Ashfields' mill and Mossfields' fiber farm were removed because their combined
building jobs exceeded starting laborers. Existing fiber RGOs and Ashfields'
fiber farm continue to support the regional textile chain.

Additional extraction investment falls from 387 to 126 across all 72 districts:
Cindermaw 129 to 46, Brackmaw 96 to 39, Reefhook 53 to 13, Shatterfin 78 to 19,
Sootwake 31 to 9. These are bonuses on top of native capacity, not total RGO
levels or output. The pass removes the old 13–19 level grants in Shatterfin and
blanket grants in small districts. Most sites receive 1–3, populous core-resource
sites up to 6, precious/secondary luxury deposits 1, and Reefhook's pearls 2.
Deposits retain their native value; these bonuses do not grant treasury income.

## Installed vanilla comparisons

The reproducible tools/economy_reference.py audit includes settlement templates
and explicit country-owned buildings on starting owned land. It excludes subject
economies, foreign buildings, later construction and engine-generated additions.

| Reference | Starting owned population | Explicit building levels |
| --- | ---: | ---: |
| Serbia | 904,565 | 55 |
| Brittany | 1,079,515 | 27 |
| Navarre | 215,135 | 41 |
| Scotland | 202,307 | 31 |
| Cyprus | 156,380 | 15 |

Cindermaw's 47 levels are below Serbia's 55 and scale similarly by population.
Brackmaw's 36 sit near Navarre's 41 with more population and a younger, rural
economy. Shatterfin starts below Scotland/Navarre in total infrastructure but
concentrates its capital in maritime production. Reefhook and Sootwake's 12 levels
are close to Cyprus's 15 at smaller populations. Naxos and Rhodes are also audited
but are much smaller population references, not targets. Brittany demonstrates
why population alone is not a linear building formula.

Building counts are a broad infrastructure comparison, not GDP equivalence:
temples, castles, villages and guilds differ in employment, cost and production.
Real balance also depends on prices, market access, RGO staffing, food, taxes and
military costs. No income or sustainable-army claim follows from these counts.

## Verification and campaign acceptance

Run `python tools/verify_economy.py --game "PATH/TO/EU5/game"` for a focused setup
build. Its report checks native ranks/resources, exact generated building levels,
population totals, differentiation, building staffing, shared-market setup and
once-only ownership-guarded extraction investment. The full build also includes
the audit in its economy report.

Static checks pass. Population remains 1,618,696. No economic building has a
class-level starting worker deficit. Hooktooth's pre-existing stockade has 100
soldier jobs and no seeded soldiers; actual garrison behavior needs testing.
Staffing checks exclude RGO jobs, migration, promotion and military levies.

In a fresh 1337 campaign record every crown at start, after the first monthly
pulse, after 12 months and after five peaceful years. Check:

- Food balance and reserves, especially Reefhook and Shatterfin.
- Market access, input shortages, building employment/profit and RGO utilization.
- Treasury balance with starting forces, debt, and the ability to fund one useful
  economic investment without subsidies or immediate conquest.
- Export roles: Cindermaw tools/weapons, Brackmaw provisions/naval supplies,
  Reefhook fish/pearls, Shatterfin maritime industry, Sootwake lumber/coal.
- Save/reload does not repeat investment; smaller crowns remain playable.

No full release build, installation, game launch or gameplay acceptance has been
performed for this pass. Retune from those observations before packaging 0.5.6.
