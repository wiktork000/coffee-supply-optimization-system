import os

from amplpy import AMPL, modules

from coffee_optimizer.models import (
    CorrectionItem,
    CorrectionOptimizationRequest,
    CorrectionOptimizationResult,
    InventoryLevel,
    OrderItem,
)

_SOLVE_STATUS_MAP = {
    "solved": "Optimal",
    "infeasible": "Infeasible",
    "unbounded": "Unbounded",
}

_CORRECTION_AMPL_MODEL = r"""
    set T ordered;
    set D;
    set B;
    set L ordered;

    param V_max {B} >= 0;
    param Q {D, L} >= 0;
    param P0 {D, T} >= 0 default 0;
    param P {D, T, L} >= 0 default 0;
    param C_fix {D, B} >= 0 default 0;
    param Demand {B, T} >= 0;
    param I0 {B} >= 0;
    param alpha >= 0, <= 1;
    param S_avail {D, T} >= 0 default 0;
    param S_max = max {d in D, t in T} S_avail[d,t];
    param LT {D, B} >= 0 integer default 0;
    param H_arrival {D, B, T} >= 0 default 0;

    # Wcześniej zaplanowane zamówienia
    param x0_prev {D, B, T} >= 0 default 0;
    param x_prev {D, B, T, L} >= 0 default 0;

    # Koszt i limit korekty
    param K_corr {D, B, T} >= 0 default 0;
    param R_max {D, B, T} >= 0 default Infinity;

    # Korekty pod pierwszym progiem
    var r0_plus {D, B, T} >= 0;
    var r0_minus {D, B, T} >= 0;

    # Korekty nad progami rabatowymi
    var r_plus {D, B, T, L} >= 0;
    var r_minus {D, B, T, L} >= 0;

    # Zamówienia końcowe po korekcie
    var x0_final {D, B, T} >= 0;
    var x_final {D, B, T, L} >= 0;

    # Magazyn i zmienne binarne
    var I {B, 0..card(T)} >= 0;
    var y_skl {D, B, T} binary;
    var y_rab {D, B, T, L} binary;

    # Powiązanie zamówienia końcowego z wcześniejszym planem i korektą
    s.t. Define_x0_final {d in D, b in B, t in T}:
        x0_final[d,b,t] =
            x0_prev[d,b,t] + r0_plus[d,b,t] - r0_minus[d,b,t];

    s.t. Define_x_final {d in D, b in B, t in T, l in L}:
        x_final[d,b,t,l] =
            x_prev[d,b,t,l] + r_plus[d,b,t,l] - r_minus[d,b,t,l];

    # Maksymalna dopuszczalna wielkość korekty
    s.t. Max_Correction {d in D, b in B, t in T}:
        r0_plus[d,b,t] + r0_minus[d,b,t]
        + sum {l in L} (r_plus[d,b,t,l] + r_minus[d,b,t,l])
        <= R_max[d,b,t];

    # Funkcja celu: koszt zamówień po korekcie + koszt korekt
    minimize Total_Cost:
        sum {t in T, b in B, d in D}
            P0[d,t] * x0_final[d,b,t]

        + sum {t in T, b in B, d in D, l in L}
            P[d,t,l] * x_final[d,b,t,l]

        + sum {t in T, b in B, d in D}
            C_fix[d,b] * y_skl[d,b,t]

        + sum {t in T, b in B, d in D}
            K_corr[d,b,t] *
            (
                r0_plus[d,b,t] + r0_minus[d,b,t]
                + sum {l in L} (r_plus[d,b,t,l] + r_minus[d,b,t,l])
            );

    # Stan początkowy magazynu
    s.t. Init_Inv {b in B}:
        I[b,0] = I0[b];

    # Bilans zapasów po korekcie
    s.t. Inv_Balance {b in B, t in T}:
        I[b,ord(t)] =
            (1 - alpha) * I[b,ord(t)-1]

            + sum {d in D, tau in T:
                ord(tau) + LT[d,b] == ord(t)}
                x0_final[d,b,tau]

            + sum {d in D, l in L, tau in T:
                ord(tau) + LT[d,b] == ord(t)}
                x_final[d,b,tau,l]

            + sum {d in D}
                H_arrival[d,b,t]

            - Demand[b,t];

    # Pojemność magazynu
    s.t. Max_Inv_Limit {b in B, t in T}:
        I[b,ord(t)] <= V_max[b];

    # Powiązanie zamówienia z kosztem stałym
    s.t. Link_Order_Binary {d in D, b in B, t in T}:
        x0_final[d,b,t] + sum {l in L} x_final[d,b,t,l]
        <= S_avail[d,t] * y_skl[d,b,t];

    s.t. Min_Order_Quantity {d in D, b in B, t in T}:
        x0_final[d,b,t] + sum {l in L} x_final[d,b,t,l]
        >= 0.001 * y_skl[d,b,t];

    # Dostępność dystrybutora
    s.t. Max_Availability {d in D, t in T}:
        sum {b in B}
            (
                x0_final[d,b,t]
                + sum {l in L} x_final[d,b,t,l]
            )
        <= S_avail[d,t];

    # Ilość poniżej pierwszego progu
    s.t. Threshold_0_Max {d in D, b in B, t in T}:
        x0_final[d,b,t] <= Q[d,first(L)];

    s.t. Threshold_0_Min {d in D, b in B, t in T}:
        x0_final[d,b,t] >= Q[d,first(L)] * y_rab[d,b,t,first(L)];

    # Ilości między progami
    s.t. Threshold_L_Max_Normal {d in D, b in B, t in T, l in L: l <> last(L)}:
        x_final[d,b,t,l] <=
            (Q[d,next(l,L)] - Q[d,l]) * y_rab[d,b,t,l];

    # Ostatni próg
    s.t. Threshold_L_Max_Last {d in D, b in B, t in T, l in L: l == last(L)}:
        x_final[d,b,t,l] <= S_max * y_rab[d,b,t,l];

    # Nie można wejść w wyższy próg bez wypełnienia niższego
    s.t. Threshold_L_Min_Normal {d in D, b in B, t in T, l in L: l <> last(L)}:
        x_final[d,b,t,l] >=
            (Q[d,next(l,L)] - Q[d,l]) * y_rab[d,b,t,next(l,L)];
"""


def _build_correction_ampl_data(request: CorrectionOptimizationRequest) -> dict:
    T = request.planning_days
    D = [d.id for d in request.distributors]
    B = [b.id for b in request.buildings]

    all_levels: set[int] = set()
    for dist in request.distributors:
        for dp in dist.daily_prices:
            for tier in dp.discount_tiers:
                all_levels.add(tier.level)

    if not all_levels:
        raise ValueError(
            "At least one discount tier is required across all distributors"
        )

    L = sorted(all_levels)

    # Q[distributor, level] = quantity threshold; per-distributor tier structure
    Q: dict[tuple, float] = {}
    for dist in request.distributors:
        for dp in dist.daily_prices:
            for tier in dp.discount_tiers:
                Q.setdefault((dist.id, tier.level), tier.quantity_kg)
    # Ensure every (distributor, level) in D x L is defined and non-decreasing in
    # level: a distributor missing a level inherits the previous level's
    # threshold (a zero-width band), so AMPL never sees an undefined Q[d,l].
    for dist in request.distributors:
        prev = 0.0
        for level in L:
            prev = Q.setdefault((dist.id, level), prev)

    P0: dict[tuple, float] = {}
    S_avail: dict[tuple, float] = {}
    P: dict[tuple, float] = {}
    T_set = set(T)

    for dist in request.distributors:
        for dp in dist.daily_prices:
            if dp.day not in T_set:
                continue
            P0[(dist.id, dp.day)] = dp.base_price
            S_avail[(dist.id, dp.day)] = dp.availability_kg

            tier_prices = {tier.level: tier.unit_price for tier in dp.discount_tiers}
            for level in L:
                P[(dist.id, dp.day, level)] = tier_prices.get(level, dp.base_price)

    C_fix: dict[tuple, float] = {}
    LT: dict[tuple, int] = {}

    for dist in request.distributors:
        for dp in dist.delivery_params:
            C_fix[(dist.id, dp.building_id)] = dp.fixed_cost_pln
            LT[(dist.id, dp.building_id)] = dp.lead_time_days

    V_max = {b.id: b.max_capacity_kg for b in request.buildings}
    I0 = {b.id: b.initial_inventory_kg for b in request.buildings}

    Demand: dict[tuple, float] = {}
    for building in request.buildings:
        for dd in building.daily_demand:
            if dd.day in T_set:
                Demand[(building.id, dd.day)] = dd.demand_kg

    H_arrival: dict[tuple, float] = {
        (ha.distributor_id, ha.building_id, ha.day): ha.quantity_kg
        for ha in request.historical_arrivals
        if ha.day in T_set
    }

    x0_prev: dict[tuple, float] = {}
    x_prev: dict[tuple, float] = {}

    for order in request.previous_orders:
        if order.day not in T_set:
            continue
        if order.threshold_level == 0:
            x0_prev[(order.distributor_id, order.building_id, order.day)] = (
                order.quantity_kg
            )
        else:
            x_prev[
                (
                    order.distributor_id,
                    order.building_id,
                    order.day,
                    order.threshold_level,
                )
            ] = order.quantity_kg

    K_corr: dict[tuple, float] = {
        (item.distributor_id, item.building_id, item.day): item.cost_per_kg + 0.01
        for item in request.correction_costs
        if item.day in T_set
    }

    R_max: dict[tuple, float] = {
        (item.distributor_id, item.building_id, item.day): item.max_correction_kg
        for item in request.correction_limits
        if item.day in T_set
    }

    return {
        "T": T,
        "D": D,
        "B": B,
        "L": L,
        "alpha": request.decay_rate,
        "V_max": V_max,
        "Q": Q,
        "I0": I0,
        "P0": P0,
        "P": P,
        "C_fix": C_fix,
        "Demand": Demand,
        "S_avail": S_avail,
        "LT": LT,
        "H_arrival": H_arrival,
        "x0_prev": x0_prev,
        "x_prev": x_prev,
        "K_corr": K_corr,
        "R_max": R_max,
    }


def _load_correction_ampl(ampl: AMPL, data: dict) -> None:
    ampl.eval(_CORRECTION_AMPL_MODEL)

    ampl.get_set("T").set_values(data["T"])
    ampl.get_set("D").set_values(data["D"])
    ampl.get_set("B").set_values(data["B"])
    ampl.get_set("L").set_values(data["L"])

    ampl.get_parameter("alpha").set(data["alpha"])
    ampl.get_parameter("V_max").set_values(data["V_max"])
    ampl.get_parameter("Q").set_values(data["Q"])
    ampl.get_parameter("I0").set_values(data["I0"])
    ampl.get_parameter("P0").set_values(data["P0"])
    ampl.get_parameter("P").set_values(data["P"])
    ampl.get_parameter("C_fix").set_values(data["C_fix"])
    ampl.get_parameter("Demand").set_values(data["Demand"])
    ampl.get_parameter("S_avail").set_values(data["S_avail"])
    ampl.get_parameter("LT").set_values(data["LT"])

    if data["H_arrival"]:
        ampl.get_parameter("H_arrival").set_values(data["H_arrival"])

    if data["x0_prev"]:
        ampl.get_parameter("x0_prev").set_values(data["x0_prev"])

    if data["x_prev"]:
        ampl.get_parameter("x_prev").set_values(data["x_prev"])

    if data["K_corr"]:
        ampl.get_parameter("K_corr").set_values(data["K_corr"])

    if data["R_max"]:
        ampl.get_parameter("R_max").set_values(data["R_max"])


def _extract_correction_results(ampl: AMPL, data: dict) -> CorrectionOptimizationResult:
    solve_result = str(ampl.get_value("solve_result"))
    status = _SOLVE_STATUS_MAP.get(solve_result, "Not Solved")

    if status != "Optimal":
        return CorrectionOptimizationResult(
            status=status,
            solver_message=solve_result,
        )

    final_orders: list[OrderItem] = []
    corrections: list[CorrectionItem] = []
    inventory_levels: list[InventoryLevel] = []

    x0_final_vals: dict = ampl.get_variable("x0_final").get_values().to_dict()
    x_final_vals: dict = ampl.get_variable("x_final").get_values().to_dict()

    r0_plus_vals: dict = ampl.get_variable("r0_plus").get_values().to_dict()
    r0_minus_vals: dict = ampl.get_variable("r0_minus").get_values().to_dict()
    r_plus_vals: dict = ampl.get_variable("r_plus").get_values().to_dict()
    r_minus_vals: dict = ampl.get_variable("r_minus").get_values().to_dict()

    I_vals: dict = ampl.get_variable("I").get_values().to_dict()

    eps = 1e-6

    for (d, b, t), val in x0_final_vals.items():
        if val > eps:
            final_orders.append(
                OrderItem(
                    distributor_id=str(d),
                    building_id=str(b),
                    day=int(t),
                    threshold_level=0,
                    quantity_kg=round(float(val), 3),
                )
            )

    for (d, b, t, lvl), val in x_final_vals.items():
        if val > eps:
            final_orders.append(
                OrderItem(
                    distributor_id=str(d),
                    building_id=str(b),
                    day=int(t),
                    threshold_level=int(lvl),
                    quantity_kg=round(float(val), 3),
                )
            )

    for (d, b, t), val in r0_plus_vals.items():
        if val > eps:
            corrections.append(
                CorrectionItem(
                    distributor_id=str(d),
                    building_id=str(b),
                    day=int(t),
                    threshold_level=0,
                    type="increase",
                    quantity_kg=round(float(val), 3),
                )
            )

    for (d, b, t), val in r0_minus_vals.items():
        if val > eps:
            corrections.append(
                CorrectionItem(
                    distributor_id=str(d),
                    building_id=str(b),
                    day=int(t),
                    threshold_level=0,
                    type="decrease",
                    quantity_kg=round(float(val), 3),
                )
            )

    for (d, b, t, lvl), val in r_plus_vals.items():
        if val > eps:
            corrections.append(
                CorrectionItem(
                    distributor_id=str(d),
                    building_id=str(b),
                    day=int(t),
                    threshold_level=int(lvl),
                    type="increase",
                    quantity_kg=round(float(val), 3),
                )
            )

    for (d, b, t, lvl), val in r_minus_vals.items():
        if val > eps:
            corrections.append(
                CorrectionItem(
                    distributor_id=str(d),
                    building_id=str(b),
                    day=int(t),
                    threshold_level=int(lvl),
                    type="decrease",
                    quantity_kg=round(float(val), 3),
                )
            )

    for (b, t), val in I_vals.items():
        if int(t) > 0:
            inventory_levels.append(
                InventoryLevel(
                    building_id=str(b),
                    day=int(t),
                    level_kg=round(float(val), 3),
                )
            )

    total_cost = float(ampl.get_objective("Total_Cost").value())

    # Calculate breakdown
    purchase_base = 0.0
    purchase_actual = 0.0
    fixed_delivery = 0.0

    # We need P0, P, C_fix from data
    P0 = data["P0"]
    P = data["P"]
    C_fix = data["C_fix"]

    for (d, b, t), val in x0_final_vals.items():
        if val > eps:
            p0 = P0.get((d, t), 0.0)
            purchase_base += p0 * val
            purchase_actual += p0 * val

    for (d, b, t, lvl), val in x_final_vals.items():
        if val > eps:
            p0 = P0.get((d, t), 0.0)
            p_disc = P.get((d, t, lvl), p0)
            purchase_base += p0 * val
            purchase_actual += p_disc * val

    y_vals: dict = ampl.get_variable("y_skl").get_values().to_dict()
    for (d, b, t), val in y_vals.items():
        if val > 0.5:
            fixed_delivery += C_fix.get((d, b), 0.0)

    return CorrectionOptimizationResult(
        status="Optimal",
        total_cost_pln=total_cost,
        solver_message=solve_result,
        final_orders=final_orders,
        corrections=corrections,
        inventory_levels=inventory_levels,
    )


def run_correction_optimization(
    request: CorrectionOptimizationRequest,
) -> CorrectionOptimizationResult:
    data = _build_correction_ampl_data(request)

    modules.load()

    license_key = os.environ.get("AMPL_LICENSE_KEY")
    if license_key:
        modules.activate(license_key)

    ampl = AMPL()

    try:
        _load_correction_ampl(ampl, data)
        ampl.set_option("solver", "cbc")
        ampl.solve()
        return _extract_correction_results(ampl, data)
    finally:
        ampl.close()
