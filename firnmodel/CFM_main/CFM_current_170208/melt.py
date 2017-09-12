from constants import *
import numpy as np

def simple_melt(self, iii):

	
    if self.bdotSec[iii]<=self.snowmeltSec[iii]: # more melt than accumulation; no new accumulation; runoff from old box

        meltdiff = self.snowmeltSec[iii] - self.bdotSec[iii] # units m ice.
        # melt_mass = meltdiff * RHO_I *S_PER_YEAR

        self.age = self.age + self.dt
        self.dz_old = self.dz
        self.sdz_old = np.sum(self.dz) # old total column thickness
        self.z_old = self.z
        self.dz = self.mass / self.rho * self.dx
        self.sdz_new = np.sum(self.dz) #total column thickness after densification, before new snow addedv
        self.z = self.dz.cumsum(axis = 0)
        self.z = self.z - self.z[0]
        self.dzNew = 0
        # if self.rho[0]>=800: # old surface is ice, so just runoff
        #     self.dz = self.mass / self.rho * self.dx
        #     self.sdz_new = np.sum(self.dz) #total column thickness after densification, before new snow added


        # else:
        
    elif self.bdotSec[iii]>self.snowmeltSec[iii]: # more accumulation than melt; all melt is from that year's accumulation; remaining accumulation is added
	    self.age = np.concatenate(([0,0],self.age[:-2]))+self.dt
	    self.dz_old = self.dz
	    self.sdz_old = np.sum(self.dz) # old total column thickness
	    self.z_old = self.z
	    self.dzNewSnow = (self.bdotSec[iii]-self.snowmeltSec[iii]) * RHO_I / self.rhos0[iii] * S_PER_YEAR
	    self.dzNewIce = self.snowmeltSec[iii] * S_PER_YEAR
	    self.dz = self.mass / self.rho * self.dx
	    self.sdz_new = np.sum(self.dz) #total column thickness after densification, before new snow added
	    self.dz = np.concatenate(([self.dzNewSnow,self.dzNewIce], self.dz[:-2]))
	    self.z = self.dz.cumsum(axis = 0)
	    self.z = np.concatenate(([0], self.z[:-1]))
	    self.rhos0[iii]=400.0
	    self.rho  = np.concatenate(([self.rhos0[iii],RHO_I], self.rho[:-2])) 
	    massNewSnow = self.bdotSec[iii] * S_PER_YEAR * RHO_I
	    massNewIce = self.snowmeltSec[iii] * S_PER_YEAR *RHO_I
	    self.mass = np.concatenate(([massNewSnow,massNewIce], self.mass[:-2]))
	    self.dzNew = self.dzNewIce + self.dzNewSnow

def percolation(self, iii):
	
	# print('!!! iii ', iii)
	porosity = 1 - self.rho/RHO_I #porosity
	dz_old = self.dz
	# print 'porosity', porosity

	porespace_0 			= porosity * self.dz #porosity in meters of each box


	melt_volume_IE  	= self.snowmeltSec[iii] * S_PER_YEAR #meters
	melt_volume_WE		= melt_volume_IE * 0.917 #meters
	melt_mass			= melt_volume_WE * 1000. #kg

	heat_to_freeze 		= melt_mass * LF_I #amount of heat needed to refreeze the melt (J)

	# print('melt_mass (orig)', melt_mass)
	if (self.mass_sum==melt_mass).any():
		exactmass = True
	else:
		exactmass = False

	ind1a = np.where(self.mass_sum<=melt_mass)[0] # indicies of boxes that will be melted away
	# if iii>1020:
	# 	print(iii)
	# 	print(self.T_mean)
	# 	print('melt_mass', melt_mass)
	# 	print('mass_sum', self.mass_sum[0:20])
	num_boxes_melted = len(ind1a)+1 #number of boxes that melt away, include the box that is partially melted
	# print('num_boxes_melted', num_boxes_melted)
	ind1 = np.where(self.mass_sum>melt_mass)[0][0] # index which will become the new surface
	# print('ind1a', ind1a)
	# print('num_boxes_melted',num_boxes_melted)
	# print('ind1', ind1)
	# print('self.mass_sum[ind1-1]',self.mass_sum[ind1])
	# print('melt_mass', melt_mass)

	# pm is the partial melt (the box/volume that has a portion melted away)
	pm_mass = self.mass_sum[ind1] - melt_mass # the remaining mass of the PM box
	pm_dz = pm_mass / self.rho[ind1] #remaining thickness
	pm_porespace = (1 - self.rho[ind1]/RHO_I) * pm_dz #porespace in the PM box
	pm_rho = self.rho[ind1] #density of the PM box

	# print('pm_mass', pm_mass)
	# print('pm_dz', pm_dz)
	# print('pm_porespace', pm_porespace)
	# print('pm_rho', pm_rho)

	cold_content_0 		= CP_I * self.mass * (K_TO_C - self.Tz) #cold content of each box, i.e. how much heat to bring it to 273K
	cold_content_0_sum = cold_content_0.cumsum(axis=0)
	cold_content = cold_content_0[ind1:] #just the boxes that don't melt away
	cold_content[0]  = CP_I * pm_mass * (K_TO_C - self.Tz[ind1]) # the partial melt box has its cold content reassigned.
	cold_content_sum 	= cold_content.cumsum(axis=0)
	# print('cold_content_sum', cold_content_sum)
	# print('heat_to_freeze', heat_to_freeze)

	ind2_rel = np.where(cold_content_sum>heat_to_freeze)[0][0] #freeze horizon index (where the wetting front freezes), index relative to ind1
	ind2 = ind2_rel + ind1 #absolute index on real grid (we have not removed the melted boxes yet)

	
	# print('rho!', self.rho[0:ind2])
	# print('rhomin', np.min(self.rho)

	if (self.rho[ind1:ind2+1]>830.0).any(): #if there is an ice lens somewhere between the new surface and where freezing should occur
		# print('!!!!!  ',iii)
		# print(self.rho[ind1:ind2+1])
		# print("blocking ice lens")
		# print('ind2 (old)', ind2)

		ind2_rel = np.where(self.rho[ind1:]>=830.0)[0][0]
		ind2 = ind2_rel + ind1 #the recalculated freezing front (water can not go past this level)
		# print('rhoind2',self.rho[ind2])

		# print('ind2 (new)', ind2)
		# print('ind2_rel (new)', ind2_rel)
		# cold_content_lens = cold_content_0[ind1:ind2+1].sum() #cold content that is is available in space between the surface and the lens 
		cold_content_lens = cold_content[0:ind2_rel].sum() #cold content that is is available in space between the surface and the lens 
		hh = heat_to_freeze - cold_content_lens 
		# hh = cold_content_lens # how much of the liquid can be refrozen with the available cold content
		
		refreeze_mass = hh / LF_I # this is how much should be able to refreeze in the available pore space above the ice lens.

		# print('melt_mass', melt_mass)
		# print('refreeze_mass', refreeze_mass)

		melt_volume_WE = refreeze_mass / 1000.
		melt_volume_IE = melt_volume_WE / 0.917 #the volume of melt that is not runoff
		runoff_volume_duetolens = melt_mass - refreeze_mass

	else:
		runoff_volume_duetolens	 = 0.0
		# print('ind2 (no change)', ind2)
		# print('ind2_rel (no change)', ind2_rel)

	# print('ind2',ind2)

	pore_indices = np.arange(ind1,ind2+1) # indicies of the boxes that are available to fill with water
	pore_indices_flip = np.flipud(pore_indices)

	# print('pore_indices', pore_indices)
	# print('dz', self.dz[ind1:ind2+1])

	porespace_0[ind1] = pm_porespace
	porespace_0_sum		= porespace_0.cumsum(axis=0)
	# print('porespace_0_sum', porespace_0_sum)
	# print('porespace_0',porespace_0)
	# print('ind1+1',ind1+1)
	# print('ind2+1',ind2+1)
	porespace = porespace_0[ind1+1:ind2+1] #space available for the water

	# print 	'porespace1', porespace
	# porespace[0]=pm_porespace
	# print 'porespace2', porespace
	porespace_sum = porespace.cumsum(axis=0)
	# print('pss', porespace_sum)
	porespace_sum_flip = (np.flipud(porespace)).cumsum(axis=0)

	# if self.rho[ind1:ind2].any()>= 830.0:
	# 	''
	# ind2a = ind2 - ind1
	# print 'ind2a', ind2a

	# print 'porespace_sum', porespace_0_sum[ind2a]-porespace_0_sum[ind1]
	# print 'melt_volume', melt_volume_IE
	available_space = porespace_0_sum[ind2]-porespace_0_sum[ind1]

	# print('available_space', available_space)
	# print('melt_volume_IE',melt_volume_IE)

	# if porespace_sum[ind2a]<melt_volume_IE:
	if available_space < melt_volume_IE: # melt volume has already been recalculated based on how much can freeze with the cold content

		# if iii>1440:
		# 	 # or self.bdotSec[iii-1])<0:
		# 	print('iii',iii)
			
		# 	print('not enough pore space')
		# 	# if iii>1440:
		# 	print(self.bdotSec[iii]*S_PER_YEAR*12)
		# 	if self.bdotSec[iii]<0:
		# 		print('negative bdot')

		# 	print('num_boxes_melted', num_boxes_melted)
		# 	print('iii',iii)
		runoff_volume_duetolimitedporespace = (melt_volume_IE - porespace_sum) * 0.917

		self.rho[ind1:ind2+1] = 870.0 #fill all of the boxes with water.
		self.Tz[ind1:ind2+1] = 273.

		# split up last box into several
		divider = num_boxes_melted

		self.rho = np.concatenate((self.rho[ind1:-1] , self.rho[-1]*np.ones(num_boxes_melted)))
		self.age = np.concatenate((self.age[ind1:-1] , self.age[-1]*np.ones(num_boxes_melted)))
		self.dz  = np.concatenate((self.dz[ind1:-1] , self.dz[-1]/divider*np.ones(num_boxes_melted)))
		self.dz[0] = pm_dz
		self.dzn = np.concatenate((np.zeros(num_boxes_melted), self.dz[1:])) #this is not quite right because is assumes compaction for the pm box is zero.
		self.dzn = self.dzn[0:self.compboxes]
		# if (self.dz<=0).any():
		# 	print self.dz[0:ind2]
		# 	raw_input('negative dz')
		self.Tz  = np.concatenate((self.Tz[ind1:-1],self.Tz[-1]*np.ones(num_boxes_melted)))
		self.bdot_mean = np.concatenate((self.bdot_mean[ind1:-1],self.bdot_mean[-1]*np.ones(num_boxes_melted)))
		self.z = self.dz.cumsum(axis = 0)
		self.z = np.concatenate(([0], self.z[:-1]))
		self.mass = self.rho*self.dz
		if len(self.mass)!=self.gridLen:
			print('num_boxes_melted', num_boxes_melted)
			print('divider',divider)
			print('ind1',ind1)
			print('ind1a',ind1a)
			print('line202')

	
	elif available_space == 0.0: #the top layer is an ice lens, so the melt runs off
		# print('ice lens on top')

		# print('rho',self.rho[0:ind1+4])

				# split up last box into several
		divider = num_boxes_melted
		# ind3 should be removed and replaced with 2 new boxes.
		self.rho = np.concatenate((self.rho[ind1:-1] , self.rho[-1]*np.ones(num_boxes_melted)))
		self.age = np.concatenate((self.age[ind1:-1] , self.age[-1]*np.ones(num_boxes_melted)))
		self.dz  = np.concatenate((self.dz[ind1:-1] , self.dz[-1]/divider*np.ones(num_boxes_melted)))
		self.dz[0] = pm_dz
		self.dzn = np.concatenate((np.zeros(num_boxes_melted), self.dz[1:])) #this is not quite right because is assumes compaction for the pm box is zero.
		self.dzn = self.dzn[0:self.compboxes]
		# if (self.dz<=0).any():
		# 	print self.dz[0:ind2]
		# 	raw_input('negative dz')
		self.Tz  = np.concatenate((self.Tz[ind1:-1],self.Tz[-1]*np.ones(num_boxes_melted)))
		self.bdot_mean = np.concatenate((self.bdot_mean[ind1:-1],self.bdot_mean[-1]*np.ones(num_boxes_melted)))
		self.z = self.dz.cumsum(axis = 0)
		self.z = np.concatenate(([0], self.z[:-1]))
		self.mass = self.rho*self.dz
		if len(self.mass)!=self.gridLen:
			print('line224')



	else:
		# if self.bdotSec[iii]<0:
		# print('iii',iii)
		# print('enough pore space')
		# print('iii',iii)
		runoff_volume_duetolimitedporespace = 0
		# print('porespace_sum_flip',porespace_sum_flip[0:5])
		# print('melt_volume_IE',melt_volume_IE)
		ind3a = np.where(porespace_sum_flip>melt_volume_IE)[0][0]
		# print(ind3a)
		ind3 = ind2 - ind3a #the index of the node that is partially filled with water

		# print 'ind3',ind3
		# print 'ind3a',ind3a
		# print 'rho3', self.rho[ind3]

		partial_volume = melt_volume_IE - np.sum(porespace_0[ind3+1:ind2+1]) # pore space filled in the box that is partially filled

		leftover_porespace = porespace_0[ind3]-partial_volume #open pore space in the the partially-filled box

		new_node_1_rho = self.rho[ind3] #split up the partial box into 2 parts
		new_node_2_rho = 870.0

		new_node_1_dz = leftover_porespace / (1 - self.rho[ind3]/RHO_I)
		new_node_2_dz = self.dz[ind3] - new_node_1_dz

		# if new_node_1_dz<0 or new_node_2_dz<0:

		# 	print 'new_node_1_dz', new_node_1_dz
		# 	print 'new_node_2_dz', new_node_2_dz
		# 	print 'leftover_porespace', leftover_porespace
		# 	print 'np.sum(porespace[ind3+1:ind2+1])', np.sum(porespace_0[ind3+1:ind2+1])
		# 	print 'dz_ind3', self.dz[ind3]
		# 	print 'porespace_ind3', porespace_0[ind3]
		# 	raw_input('negative dz new')

		self.rho[ind3+1:ind2+1] = 870.0
		self.Tz[ind1:ind2+1] = 273.

		# split up last box into several
		divider = num_boxes_melted
		# ind3 should be removed and replaced with 2 new boxes.
		self.rho = np.concatenate((self.rho[ind1:ind3] , [new_node_1_rho,new_node_2_rho] , self.rho[ind3+1:-1] , self.rho[-1]*np.ones(num_boxes_melted-1)))
				
		# if (iii>7000 and iii<7435):
		# 	print('num_boxes_melted',num_boxes_melted)
		# 	print('ind1',ind1)
		# 	print('ind2',ind2)
		# 	print('ind3',ind3)
		# 	print(available_space)
		# 	print(melt_volume_IE)
		# 	print('top',len(self.rho[ind1:ind3]))
		# 	print('new',len([new_node_1_rho,new_node_2_rho]))
		# 	print('old',len(self.rho[ind3+1:-1]))
		# 	print('bottom',len(self.rho[-1]*np.ones(num_boxes_melted-1)))
		# 	print('pm_mass',pm_mass)
		# 	print('self.mass',self.mass[0:ind2])
		# 	print('melt_mass',melt_mass)

		# if (iii>7429 and iii<7435):
			# print('rholen',len(self.rho))
		self.age = np.concatenate((self.age[ind1:ind3] , [self.age[ind3],self.age[ind3]] , self.age[ind3+1:-1] , self.age[-1]*np.ones(num_boxes_melted-1)))
		dzhold = self.dz[ind1+1:ind3]
		dzhold2 = self.dz[ind3+1:-1]
		self.dz = np.concatenate((self.dz[ind1:ind3] , [new_node_1_dz,new_node_2_dz] , self.dz[ind3+1:-1] ,self.dz[-1]/divider*np.ones(num_boxes_melted-1)))
		self.dzn = np.concatenate((np.zeros(num_boxes_melted), np.append(dzhold, new_node_1_dz+new_node_2_dz), dzhold2))
		self.dzn = self.dzn[0:self.compboxes]

		
		# print(np.min(self.dz)
		# if (self.dz<=0).any():
		# 	print self.dz[0:ind2]
		# 	raw_input('negative dz')
		self.dz[0] = pm_dz
		self.Tz = np.concatenate((self.Tz[ind1:ind3] , [self.Tz[ind3],self.Tz[ind3]] , self.Tz[ind3+1:-1] , self.Tz[-1]*np.ones(num_boxes_melted-1)))
		self.bdot_mean = np.concatenate((self.bdot_mean[ind1:ind3] , [self.bdot_mean[ind3],self.bdot_mean[ind3]] , self.bdot_mean[ind3+1:-1] , self.bdot_mean[-1]*np.ones(num_boxes_melted-1)))
		self.z = self.dz.cumsum(axis = 0)
		self.z = np.concatenate(([0], self.z[:-1]))
		self.mass = self.rho*self.dz
		# if len(self.mass)!=self.gridLen:
		# 	print('line283')

		# print('self.mass', self.mass)

		# if there is an ice lens:
			# how much water can the porous firn refreeze? the rest is runoff.


	# print('###rho###', self.rho[0:6])
	# runoff_volume = runoff_volume_duetolimitedporespace + runoff_volume_duetolens
	# print 'runoff_volume = ', runoff_volume

	return self.rho, self.age, self.dz, self.Tz, self.z, self.mass, self.dzn




