"""This represents the base model of the BSM2 group of classes.

- BSM2 base: Primary clarifier, 5 asm1 reactors, a second clarifier, sludge thickener,
adm1 fermenter, sludge dewatering and wastewater storage in dynamic simulation without any controllers.
"""

import os

import numpy as np
from tqdm import tqdm

import bsm2_python.bsm2.init.adm1init_bsm2 as adm1init
import bsm2_python.bsm2.init.asm1init_bsm2 as asm1init
import bsm2_python.bsm2.init.dewateringinit_bsm2 as dewateringinit
import bsm2_python.bsm2.init.plantperformanceinit_bsm2 as pp_init
import bsm2_python.bsm2.init.primclarinit_bsm2 as primclarinit
import bsm2_python.bsm2.init.reginit_bsm2 as reginit
import bsm2_python.bsm2.init.settler1dinit_bsm2 as settler1dinit
import bsm2_python.bsm2.init.storageinit_bsm2 as storageinit
import bsm2_python.bsm2.init.thickenerinit_bsm2 as thickenerinit
from bsm2_python.bsm2.adm1_bsm2 import ADM1Reactor
from bsm2_python.bsm2.asm1_bsm2 import ASM1Reactor
from bsm2_python.bsm2.dewatering_bsm2 import Dewatering
from bsm2_python.bsm2.helpers_bsm2 import Combiner, Splitter
from bsm2_python.bsm2.plantperformance import PlantPerformance
from bsm2_python.bsm2.primclar_bsm2 import PrimaryClarifier
from bsm2_python.bsm2.settler1d_bsm2 import Settler
from bsm2_python.bsm2.storage_bsm2 import Storage
from bsm2_python.bsm2.thickener_bsm2 import Thickener
from bsm2_python.bsm_base import BSMBase

path_name = os.path.dirname(__file__)

SI, SS, XI, XS, XBH, XBA, XP, SO, SNO, SNH, SND, XND, SALK, TSS, Q, TEMP, SD1, SD2, SD3, XD4, XD5 = np.arange(21)


class BSM2Base(BSMBase):
    """Creates a BSM2Base object. It is a base class and resembles the BSM2 model without any controllers.

    Parameters
    ----------
    data_in : np.ndarray(n, 22) | str (optional)
        Influent data. Has to be a 2D array. <br>
        First column is time [d], the rest are 21 components
        (13 ASM1 components, TSS, Q, T and 5 dummy states).
        If a string is provided, it is interpreted as a file name.
        If not provided, the influent data from BSM2 is used. \n
        [SI, SS, XI, XS, XBH, XBA, XP, SO, SNO, SNH, SND, XND, SALK, TSS, Q, TEMP, SD1, SD2, SD3, XD4, XD5]
    timestep : float (optional)
        Timestep for the simulation [d]. <br>
        If not provided, the timestep is set to 1 minute. <br>
        Please note: Due to sensor sensitivity, the timestep should not be larger than 1 minute.
    endtime : float (optional)
        Endtime for the simulation [d]. <br>
        If not provided, the endtime is the last time step in the influent data.
    evaltime : int | np.ndarray(2) (optional)
        Evaluation time for the simulation [d]. <br>
        When passed as an int, it defines the number of last days of the simulation to be evaluated.
        When passed as a 1D np.ndarray with two values, it defines the start and end time of the evaluation period.
        If not provided, the last 5 days of the simulation will be assessed. \n
        [starttime, self.simtime[-1]]
    tempmodel : bool (optional)
        If `True`, the temperature model dependencies are activated.
        Default is `False`.
    activate : bool (optional)
        If `True`, the dummy states are activated.
        Default is `False`.
    data_out : str (optional)
        Path to the output data file. <br>
        If not provided, no output data is saved.
    """

    # --8<-- [start:step_0]
    def __init__(
        self,
        data_in: np.ndarray | str | None = None,
        timestep: float | None = None,
        endtime: float | None = None,
        evaltime: int | np.ndarray | None = None,
        *,
        tempmodel: bool = False,
        activate: bool = False,
        data_out: str | None = None,
    ):
        super().__init__(
            data_in=data_in,
            timestep=timestep,
            endtime=endtime,
            evaltime=evaltime,
            data_out=data_out,
        )
        # --8<-- [end:step_0]

        # --8<-- [start:step_1]
        # definition of the objects:
        self.input_splitter = Splitter(sp_type=2)
        self.bypass_plant = Splitter()
        self.combiner_primclar_pre = Combiner()
        self.primclar = PrimaryClarifier(
            primclarinit.VOL_P,
            primclarinit.YINIT1,
            primclarinit.PAR_P,
            asm1init.PAR1,
            primclarinit.XVECTOR_P,
            tempmodel=tempmodel,
            activate=activate,
        )
        self.combiner_primclar_post = Combiner()
        # --8<-- [end:step_1]

        # --8<-- [start:step_2]
        self.bypass_reactor = Splitter()
        self.combiner_reactor = Combiner()
        self.reactor1 = ASM1Reactor(
            reginit.KLA1,
            asm1init.VOL1,
            asm1init.YINIT1,
            asm1init.PAR1,
            reginit.CARB1,
            reginit.CARBONSOURCECONC,
            tempmodel=tempmodel,
            activate=activate,
        )
        self.reactor2 = ASM1Reactor(
            reginit.KLA2,
            asm1init.VOL2,
            asm1init.YINIT2,
            asm1init.PAR2,
            reginit.CARB2,
            reginit.CARBONSOURCECONC,
            tempmodel=tempmodel,
            activate=activate,
        )
        self.reactor3 = ASM1Reactor(
            reginit.KLA3,
            asm1init.VOL3,
            asm1init.YINIT3,
            asm1init.PAR3,
            reginit.CARB3,
            reginit.CARBONSOURCECONC,
            tempmodel=tempmodel,
            activate=activate,
        )
        self.reactor4 = ASM1Reactor(
            reginit.KLA4,
            asm1init.VOL4,
            asm1init.YINIT4,
            asm1init.PAR4,
            reginit.CARB4,
            reginit.CARBONSOURCECONC,
            tempmodel=tempmodel,
            activate=activate,
        )
        self.reactor5 = ASM1Reactor(
            reginit.KLA5,
            asm1init.VOL5,
            asm1init.YINIT5,
            asm1init.PAR5,
            reginit.CARB5,
            reginit.CARBONSOURCECONC,
            tempmodel=tempmodel,
            activate=activate,
        )
        self.splitter_reactor = Splitter()
        self.settler = Settler(
            settler1dinit.DIM,
            settler1dinit.LAYER,
            asm1init.QR,
            asm1init.QW,
            settler1dinit.settlerinit,
            settler1dinit.SETTLERPAR,
            asm1init.PAR1,
            tempmodel,
            settler1dinit.MODELTYPE,
        )
        self.combiner_effluent = Combiner()
        # --8<-- [end:step_2]

        # --8<-- [start:step_3]
        self.thickener = Thickener(thickenerinit.THICKENERPAR)
        self.splitter_thickener = Splitter()
        self.combiner_adm1 = Combiner()
        self.adm1_reactor = ADM1Reactor(
            adm1init.DIGESTERINIT, adm1init.DIGESTERPAR, adm1init.INTERFACEPAR, adm1init.DIM_D
        )
        self.dewatering = Dewatering(dewateringinit.DEWATERINGPAR)
        self.storage = Storage(storageinit.VOL_S, storageinit.ystinit, tempmodel, activate)
        self.splitter_storage = Splitter()
        # --8<-- [end:step_3]

        # --8<-- [start:step_4]
        self.performance = PlantPerformance(pp_init.PP_PAR)
        # --8<-- [end:step_4]

        # --8<-- [start:step_5]
        self.y_in = self.data_in[:, 1:]

        self.ys_tss_internal = np.zeros(settler1dinit.LAYER[1])
        self.yd_out = np.zeros(51)
        self.yst_vol = 0
        (
            self.yst_sp_p,
            self.yt_sp_p,
            self.y_out1,
            self.y_out2,
            self.y_out3,
            self.y_out4,
            self.y_out5,
            self.ys_r,
            self.ys_was,
            self.ys_of,
            self.yp_uf,
            self.yp_of,
            self.yp_internal,
            self.yt_uf,
            self.yd_in,
            self.yi_out2,
            self.ydw_s,
            self.yst_out,
            self.yst_sp_as,
            self.yt_sp_as,
            self.y_out5_r,
            self.y_eff,
        ) = self._create_copies(self.y_in[0], 22)
        # --8<-- [end:step_5]

        # --8<-- [start:step_6]
        self.y_in_all = np.zeros((len(self.simtime), 21))
        self.y_eff_all = np.zeros((len(self.simtime), 21))
        self.y_in_bp_all = np.zeros((len(self.simtime), 21))
        self.to_primary_all = np.zeros((len(self.simtime), 21))
        self.prim_in_all = np.zeros((len(self.simtime), 21))
        self.qpass_plant_all = np.zeros((len(self.simtime), 21))
        self.qpassplant_to_as_all = np.zeros((len(self.simtime), 21))
        self.qpassAS_all = np.zeros((len(self.simtime), 21))
        self.to_as_all = np.zeros((len(self.simtime), 21))
        self.feed_settler_all = np.zeros((len(self.simtime), 21))
        self.qthick2AS_all = np.zeros((len(self.simtime), 21))
        self.qthick2prim_all = np.zeros((len(self.simtime), 21))
        self.qstorage2AS_all = np.zeros((len(self.simtime), 21))
        self.qstorage2prim_all = np.zeros((len(self.simtime), 21))
        self.sludge_all = np.zeros((len(self.simtime), 21))

        self.y_out1_all = np.zeros((len(self.simtime), 21))
        self.y_out2_all = np.zeros((len(self.simtime), 21))
        self.y_out3_all = np.zeros((len(self.simtime), 21))
        self.y_out4_all = np.zeros((len(self.simtime), 21))
        self.y_out5_all = np.zeros((len(self.simtime), 21))
        self.ys_r_all = np.zeros((len(self.simtime), 21))
        self.ys_was_all = np.zeros((len(self.simtime), 21))
        self.ys_of_all = np.zeros((len(self.simtime), 21))
        self.ys_tss_internal_all = np.zeros((len(self.simtime), settler1dinit.LAYER[1]))
        self.yp_uf_all = np.zeros((len(self.simtime), 21))
        self.yp_of_all = np.zeros((len(self.simtime), 21))
        self.yi_out2_all = np.zeros((len(self.simtime), 21))
        self.yst_out_all = np.zeros((len(self.simtime), 21))
        self.yst_vol_all = np.zeros((len(self.simtime), 2))
        self.ydw_s_all = np.zeros((len(self.simtime), 21))
        self.yt_uf_all = np.zeros((len(self.simtime), 21))
        self.yp_internal_all = np.zeros((len(self.simtime), 21))
        self.yd_out_all = np.zeros((len(self.simtime), 51))
        self.yt_uf_all = np.zeros((len(self.simtime), 21))
        # --8<-- [end:step_6]

        # --8<-- [start:step_7]
        self.klas = np.array([reginit.KLA1, reginit.KLA2, reginit.KLA3, reginit.KLA4, reginit.KLA5])
        # scenario 5, 75th percentile, 50% reduction when S_NH below 4g/m3
        # self.controller = ControllerOxygen(self.timestep[0], 0.75, klas, 0.5, 4)

        self.sludge_height = 0

        self.ae = 0
        self.pe = 0
        self.me = 0
        self.heat_demand = 0
        self.iqi_all = np.zeros(len(self.simtime))
        self.eqi_all = np.zeros(len(self.simtime))
        self.oci_all = np.zeros(len(self.simtime))
        self.perf_factors_all = np.zeros((len(self.simtime), 12))
        self.violation_all = np.zeros(len(self.simtime))

        self.qintr = asm1init.QINTR
        self.y_out5_r[14] = self.qintr
        # --8<-- [end:step_7]

    # --8<-- [start:step_8]
    def step(self, i: int, *args, **kwargs):
        # --8<-- [end:step_8]
        """Simulates one time step of the BSM2 model.

        Parameters
        ----------
        i : int
            Index of the current time step [-].
        """

        # --8<-- [start:step_9]
        # timestep = timesteps[i]
        step: float = self.simtime[i]
        stepsize: float = self.timesteps[i]

        self.reactor1.kla, self.reactor2.kla, self.reactor3.kla, self.reactor4.kla, self.reactor5.kla = self.klas
        # --8<-- [end:step_9]

        # --8<-- [start:step_10]
        # get influent data that is smaller than and closest to current time step
        y_in_timestep = self.y_in[np.where(self.data_time <= step)[0][-1], :]

        iqi = self.performance.iqi(y_in_timestep)[0]
        self.iqi_all[i] = iqi
        # --8<-- [end:step_10]

        # --8<-- [start:step_11]
        yp_in_c, y_in_bp = self.input_splitter.output(y_in_timestep, (0.0, 0.0), float(reginit.QBYPASS))
        y_plant_bp, y_in_as_c = self.bypass_plant.output(y_in_bp, (1 - reginit.QBYPASSPLANT, reginit.QBYPASSPLANT))

        yp_in = self.combiner_primclar_pre.output(yp_in_c, self.yst_sp_p, self.yt_sp_p)
        self.yp_uf, self.yp_of, self.yp_internal = self.primclar.output(stepsize, step, yp_in)
        y_c_as_bp = self.combiner_primclar_post.output(self.yp_of[:21], y_in_as_c)
        # --8<-- [end:step_11]

        # --8<-- [start:step_12]
        y_bp_as, y_as_bp_c_eff = self.bypass_reactor.output(y_c_as_bp, (1 - reginit.QBYPASSAS, reginit.QBYPASSAS))
        y_in1 = self.combiner_reactor.output(self.ys_r, y_bp_as, self.yst_sp_as, self.yt_sp_as, self.y_out5_r)
        self.y_out1 = self.reactor1.output(stepsize, step, y_in1)
        self.y_out2 = self.reactor2.output(stepsize, step, self.y_out1)
        self.y_out3 = self.reactor3.output(stepsize, step, self.y_out2)
        self.y_out4 = self.reactor4.output(stepsize, step, self.y_out3)
        self.y_out5 = self.reactor5.output(stepsize, step, self.y_out4)
        ys_in, self.y_out5_r = self.splitter_reactor.output(
            self.y_out5, (max(self.y_out5[14] - self.qintr, 0.0), float(self.qintr))
        )
        self.ys_r, self.ys_was, self.ys_of, _, self.ys_tss_internal = self.settler.output(stepsize, step, ys_in)
        # --8<-- [end:step_12]

        # --8<-- [start:step_13]
        self.y_eff = self.combiner_effluent.output(y_plant_bp, y_as_bp_c_eff, self.ys_of)

        eqi = self.performance.eqi(self.ys_of, y_plant_bp, y_as_bp_c_eff)[0]
        self.eqi_all[i] = eqi

        self.yt_uf, yt_of = self.thickener.output(self.ys_was)
        self.yt_sp_p, self.yt_sp_as = self.splitter_thickener.output(
            yt_of, (1 - reginit.QTHICKENER2AS, reginit.QTHICKENER2AS)
        )
        # --8<-- [end:step_13]

        # --8<-- [start:step_14]
        self.yd_in = self.combiner_adm1.output(self.yt_uf, self.yp_uf)
        self.yi_out2, self.yd_out, _ = self.adm1_reactor.output(stepsize, step, self.yd_in, reginit.T_OP)

        self.ydw_s, ydw_r = self.dewatering.output(self.yi_out2)

        self.yst_out, self.yst_vol = self.storage.output(stepsize, step, ydw_r, reginit.QSTORAGE)
        self.yst_sp_p, self.yst_sp_as = self.splitter_storage.output(
            self.yst_out, (1 - reginit.QSTORAGE2AS, reginit.QSTORAGE2AS)
        )
        # --8<-- [end:step_14]

        # --8<-- [start:step_15]
        vol = np.array(
            [
                self.reactor1.volume,
                self.reactor2.volume,
                self.reactor3.volume,
                self.reactor4.volume,
                self.reactor5.volume,
                self.adm1_reactor.volume_liq,
            ]
        )
        sosat = np.array([asm1init.SOSAT1, asm1init.SOSAT2, asm1init.SOSAT3, asm1init.SOSAT4, asm1init.SOSAT5])
        self.ae = self.performance.aerationenergy_step(self.klas, vol[0:5], sosat)
        flows = np.array([self.qintr, asm1init.QR, asm1init.QW, self.yp_uf[14], self.yt_uf[14], self.ydw_s[14]])
        self.pe = self.performance.pumpingenergy_step(flows, pp_init.PP_PAR[10:16])
        self.me = self.performance.mixingenergy_step(self.klas, vol, pp_init.PP_PAR[16])
        # --8<-- [end:step_15]

        # --8<-- [start:step_16]
        tss_mass = self.performance.tss_mass_bsm2(
            self.yp_of,
            self.yp_uf,
            self.yp_internal,
            self.y_out1,
            self.y_out2,
            self.y_out3,
            self.y_out4,
            self.y_out5,
            self.ys_tss_internal,
            self.yd_out,
            self.yst_out,
            self.yst_vol,
        )
        # --8<-- [end:step_16]

        # --8<-- [start:step_17]
        ydw_s_tss_flow = self.performance.tss_flow(self.ydw_s)
        y_eff_tss_flow = self.performance.tss_flow(self.y_eff)
        carb = reginit.CARB1 + reginit.CARB2 + reginit.CARB3 + reginit.CARB4 + reginit.CARB5
        added_carbon_mass = self.performance.added_carbon_mass(carb, reginit.CARBONSOURCECONC)
        self.heat_demand = self.performance.heat_demand_step(self.yd_in, reginit.T_OP)[0]
        ch4_prod, h2_prod, co2_prod, q_gas = self.performance.gas_production(self.yd_out, reginit.T_OP)
        # --8<-- [end:step_17]

        # --8<-- [start:step_18]
        # This calculates an approximate oci value for each time step,
        # neglecting changes in the tss mass inside the whole plant
        self.oci_all[i] = self.performance.oci(
            self.pe * 24,
            self.ae * 24,
            self.me * 24,
            ydw_s_tss_flow,
            added_carbon_mass,
            self.heat_demand * 24,
            ch4_prod,
        )
        # --8<-- [end:step_18]

        # --8<-- [start:step_19]
        # These values are used to calculate the exact performance values at the end of the simulation
        self.perf_factors_all[i, :12] = [
            self.pe * 24,
            self.ae * 24,
            self.me * 24,
            ydw_s_tss_flow,
            y_eff_tss_flow,
            tss_mass,
            added_carbon_mass,
            self.heat_demand * 24,
            ch4_prod,
            h2_prod,
            co2_prod,
            q_gas,
        ]
        # --8<-- [end:step_19]

        # --8<-- [start:step_20]
        self.y_in_all[i] = y_in_timestep
        self.y_eff_all[i] = self.y_eff
        self.y_in_bp_all[i] = y_in_bp
        self.to_primary_all[i] = yp_in_c
        self.prim_in_all[i] = yp_in
        self.qpass_plant_all[i] = y_plant_bp
        self.qpassplant_to_as_all[i] = y_in_as_c
        self.qpassAS_all[i] = y_as_bp_c_eff
        self.to_as_all[i] = y_bp_as
        self.feed_settler_all[i] = ys_in
        self.qthick2AS_all[i] = self.yt_sp_as
        self.qthick2prim_all[i] = self.yt_sp_p
        self.qstorage2AS_all[i] = self.yst_sp_as
        self.qstorage2prim_all[i] = self.yst_sp_p
        self.sludge_all[i] = self.ydw_s

        # data for calculation of final oci
        self.violation_all[i] = self.performance.violation_step(self.y_eff[SNH], 4)[0]
        self.y_out1_all[i] = self.y_out1
        self.y_out2_all[i] = self.y_out2
        self.y_out3_all[i] = self.y_out3
        self.y_out4_all[i] = self.y_out4
        self.y_out5_all[i] = self.y_out5
        self.ys_r_all[i] = self.ys_r
        self.ys_was_all[i] = self.ys_was
        self.ys_of_all[i] = self.ys_of
        self.ys_tss_internal_all[i] = self.ys_tss_internal
        self.yp_uf_all[i] = self.yp_uf
        self.yp_of_all[i] = self.yp_of
        self.yt_uf_all[i] = self.yt_uf
        self.yd_out_all[i] = self.yd_out
        self.yi_out2_all[i] = self.yi_out2
        self.yst_out_all[i] = self.yst_out
        self.yst_vol_all[i] = self.yst_vol, step
        self.ydw_s_all[i] = self.ydw_s
        self.yp_internal_all[i] = self.yp_internal
        # --8<-- [end:step_20]

    def stabilize(self, atol: float = 1e-3):
        """Stabilizes the plant.

        Parameters
        ----------
        atol : float (optional)
            Absolute tolerance for the stabilization. <br>
            Default is 1e-3.

        Returns
        -------
        stable : bool
            Returns `True` if plant is stabilized after iterations.
        """
        check_vars = [
            'y_eff',
            'y_out1',
            'y_out2',
            'y_out3',
            'y_out4',
            'y_out5',
            'yt_sp_as',
            'yt_sp_p',
            'yst_sp_as',
            'yst_sp_p',
            'ydw_s',
            'y_out1',
            'y_out2',
            'y_out3',
            'y_out4',
            'y_out5',
            'ys_of',
            'yp_uf',
        ]
        stable = super()._stabilize(check_vars=check_vars, atol=atol)
        return stable

    def simulate(self, *, plot=True, export=True):
        """Simulates the plant.

        Parameters
        ----------
        plot : bool (optional)
            If `True`, the data is plotted. <br>
            Default is `True`.
        export : bool (optional)
            If `True`, the data is exported. <br>
            Default is `True`.
        """

        for i, _ in enumerate(tqdm(self.simtime)):
            self.step(i)

            if i == 0:
                self.evaluator.add_new_data('iqi', 'iqi')
                self.evaluator.add_new_data('eqi', 'eqi')
                self.evaluator.add_new_data('oci', 'oci')
                self.evaluator.add_new_data('oci_final', 'oci_final', plot=False)
            if self.evaltime[0] <= self.simtime[i] <= self.evaltime[1]:
                self.evaluator.update_data('iqi', self.iqi_all[i], self.simtime[i])
                self.evaluator.update_data('eqi', self.eqi_all[i], self.simtime[i])
                self.evaluator.update_data('oci', self.oci_all[i], self.simtime[i])

        self.oci_final = self.get_final_performance()[-1]
        self.evaluator.update_data('oci_final', self.oci_final, self.evaltime[1])
        self.finish_evaluation(plot=plot)

    def finish_evaluation(self, *, plot=True):
        """Finishes the evaluation of the plant.

        Parameters
        ----------
        plot : bool (optional)
            If `True`, the data is plotted. <br>
            Default is `True`.
        """

        if plot:
            self.evaluator.plot_data()
        self.evaluator.export_data()

    def get_violations(self, comp: tuple = ('SNH',), lim: tuple = (4,)):
        """Returns the violations of the given components within the evaluation interval.

        Parameters
        ----------
        comp : tuple(str) (optional)
            List of components to check for violations. <br>
            Default is ('SNH').
        lim : tuple(float) (optional)
            List of limits for the components. <br>
            Default is (4).

        Returns
        -------
        violations : dict{'comp': float}
            Dictionary with the components as keys and the violation time [d].
        """

        comp_dict = {
            'SI': 0,
            'SS': 1,
            'XI': 2,
            'XS': 3,
            'XBH': 4,
            'XBA': 5,
            'XP': 6,
            'SO': 7,
            'SNO': 8,
            'SNH': 9,
            'SND': 10,
            'XND': 11,
            'SALK': 12,
            'TSS': 13,
            'Q': 14,
            'TEMP': 15,
            'SD1': 16,
            'SD2': 17,
            'SD3': 18,
            'XD4': 19,
            'XD5': 20,
        }
        if len(comp) != len(lim):
            raise ValueError('The length of comp and lim has to be the same.')
        for c in comp:
            if c not in comp_dict:
                err = f'The component {c} is not in the list of components.'
                raise ValueError(err)
        comps = [comp_dict[c] for c in comp]

        violations = {}
        for i in range(len(comp)):
            comp_eff = self.y_eff_all[self.eval_idx[0] : self.eval_idx[1], comps[i]]
            violations[comp[i]] = np.sum(self.performance.violation_step(comp_eff, lim[i])) / 60 / 24
        return violations

    def get_final_performance(self):
        """Returns the final performance values for evaluation period.

        Returns
        -------
        iqi_eval : float
            Final iqi value [kg ⋅ d⁻¹].
        eqi_eval : float
            Final eqi value [kg ⋅ d⁻¹].
        tot_sludge_prod : float
            Total sludge production [kg ⋅ d⁻¹].
        tot_tss_mass : float
            Total tss mass [kg ⋅ d⁻¹].
        carb_mass : float
            Carbon mass [kg(COD) ⋅ d⁻¹].
        ch4_prod : float
            Methane production [kg(CH4) ⋅ d⁻¹].
        h2_prod : float
            Hydrogen production [kg(H2) ⋅ d⁻¹].
        co2_prod : float
            Carbon dioxide production [kg(CO2) ⋅ d⁻¹].
        q_gas : float
            Total gas production [m³ ⋅ d⁻¹].
        heat_demand : float
            Heat demand [kWh ⋅ d⁻¹].
        mixingenergy : float
            Mixing energy [kWh ⋅ d⁻¹].
        pumpingenergy : float
            Pumping energy [kWh ⋅ d⁻¹].
        aerationenergy : float
            Aeration energy [kWh ⋅ d⁻¹].
        oci_eval : float
            Final operational cost index value [-].
        """

        # calculate the final performance values

        num_eval_timesteps = self.eval_idx[1] - self.eval_idx[0]

        iqi_eval = np.sum(self.iqi_all[self.eval_idx[0] : self.eval_idx[1]]) / num_eval_timesteps
        eqi_eval = np.sum(self.eqi_all[self.eval_idx[0] : self.eval_idx[1]]) / num_eval_timesteps

        oci_factors_eval = self.perf_factors_all[self.eval_idx[0] : self.eval_idx[1]]
        pumpingenergy = np.sum(oci_factors_eval[:, 0]) / num_eval_timesteps
        aerationenergy = np.sum(oci_factors_eval[:, 1]) / num_eval_timesteps
        mixingenergy = np.sum(oci_factors_eval[:, 2]) / num_eval_timesteps
        tot_tss_mass = np.sum(oci_factors_eval[:, 3]) / num_eval_timesteps + (
            oci_factors_eval[-1, 5] - oci_factors_eval[0, 5]
        ) / (self.evaltime[-1] - self.evaltime[0])
        tot_sludge_prod = (np.sum(oci_factors_eval[:, 4]) + np.sum(oci_factors_eval[:, 3])) / num_eval_timesteps + (
            oci_factors_eval[-1, 5] - oci_factors_eval[0, 5]
        ) / (self.evaltime[-1] - self.evaltime[0])
        carb_mass = np.sum(oci_factors_eval[:, 6]) / num_eval_timesteps
        heat_demand = np.sum(oci_factors_eval[:, 7]) / num_eval_timesteps
        ch4_prod = np.sum(oci_factors_eval[:, 8]) / num_eval_timesteps
        h2_prod = np.sum(oci_factors_eval[:, 9]) / num_eval_timesteps
        co2_prod = np.sum(oci_factors_eval[:, 10]) / num_eval_timesteps
        q_gas = np.sum(oci_factors_eval[:, 11]) / num_eval_timesteps

        oci_eval = self.performance.oci(
            pumpingenergy, aerationenergy, mixingenergy, tot_tss_mass, carb_mass, heat_demand, ch4_prod
        )

        return (
            iqi_eval,
            eqi_eval,
            tot_sludge_prod,
            tot_tss_mass,
            carb_mass,
            ch4_prod,
            h2_prod,
            co2_prod,
            q_gas,
            heat_demand,
            mixingenergy,
            pumpingenergy,
            aerationenergy,
            oci_eval,
        )
