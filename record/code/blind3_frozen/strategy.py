# strategy.py -- FROZEN deliverable of blind build 3. factory(E, seed): seed None = the primary design, integer = its random twin.
# All rules live in strat.py (class Design). Twin persistence p is the value calibrated in-sample (out/twin_p.csv).
import strat
from strat import make_factory, acct3, tools3, DATA
#                         fam      par  U    N   B  TW  twin p
CONFIG = {
    'PRIMARY': ('BLEND', 6, 400, 15, 2, 1, 0.2101),     # BLEND_p6_U400_B2_N15_T1
    'FAM_L12': ('BLEND', 12, 400, 15, 2, 1, 0.1268),    # BLEND_p12_U400_B2_N15_T1
    'FAM_U200': ('BLEND', 6, 200, 15, 2, 1, 0.2316),    # BLEND_p6_U200_B2_N15_T1
    'FAM_B4': ('BLEND', 6, 400, 15, 4, 1, 0.1783),      # BLEND_p6_U400_B4_N15_T1
    'FAM_N18': ('BLEND', 6, 400, 18, 2, 1, 0.2096),     # BLEND_p6_U400_B2_N18_T1
    'D0': ('MOM', 12, 200, 18, 4, 1, 0.1419),           # MOM_p12_U200_B4_N18_T1
}
FACTORIES = {k: make_factory(*v) for k, v in CONFIG.items()}
factory = FACTORIES['PRIMARY']
