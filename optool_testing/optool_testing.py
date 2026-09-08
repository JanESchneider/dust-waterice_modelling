import optool
import matplotlib.pyplot as plt
import numpy as np

#p = optool.particle("~/optool/optool pyr 0.8 -m h2o 0.2 -na 24 -d")
#p.plot()

sil  = optool.particle('~/optool/optool -d -a 0.001 100 0 100 ol-mg50'  ,cache='sil')
carb = optool.particle('~/optool/optool -d -a 0.001 3.0 0 50  c'        ,cache='carb')

nsil = sil.a1**(-2.5)             # power law, no normalization required
nsil[sil.a1<0.01] = 0             # no grains smaller than 0.01um
nsil[sil.a1>0.3]  = 0             # no grains larger  than 0.3um
sil_pl = sil.sizedist(nsil)       # pass the relative number for each size

nc = carb.a1**(-2.5)              # power law, no normalization required
nc[carb.a1>0.3]=0                 # no grains larger than 0.3um
carb_pl = carb.sizedist(nc)       # pass the relative number for each size

ptot = 0.7*sil_pl + 0.3*carb_pl   # weights should add up to 1
#ptot.plot()                       # plot the resulting opacity

p_ism = ptot * 0.01               # dilute the opacity
p_ism.computemean(tmax=1300)      # Compute mean opacities
p_ism.plot()                      # Plot the results

plt.show()