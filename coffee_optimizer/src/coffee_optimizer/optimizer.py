import os

from amplpy import AMPL, modules

from coffee_optimizer.models import (
    CostBreakdown,
    InventoryLevel,
    OptimizationRequest,
    OptimizationResult,
    OrderItem,
)

_SOLVE_STATUS_MAP = {
    "solved": "Optimal",
    "infeasible": "Infeasible",
    "unbounded": "Unbounded",
}

_AMPL_MODEL = r"""
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

    var x0 {D, B, T} >= 0;
    var x {D, B, T, L} >= 0;
    var I {B, 0..card(T)} >= 0;
    var y_skl {D, B, T} binary;
    var y_rab {D, B, T, L} binary;

    minimize Total_Cost:
        sum {t in T, b in B, d in D} (P0[d,t] + 1e-7) * x0[d,b,t] +
        sum {t in T, b in B, d in D, l in L} (P[d,t,l] + 1e-7) * x[d,b,t,l] +
        sum {t in T, b in B, d in D} C_fix[d,b] * y_skl[d,b,t];

    s.t. Init_Inv {b in B}:
        I[b,0] = I0[b];

    s.t. Inv_Balance {b in B, t in T}:
        I[b,ord(t)] = (1 - alpha) * I[b,ord(t)-1]
            + sum {d in D, tau in T: ord(tau) + LT[d,b] == ord(t)} x0[d,b,tau]
            + sum {d in D, l in L, tau in T: ord(tau) + LT[d,b] == ord(t)} x[d,b,tau,l]
            + sum {d in D} H_arrival[d,b,t]
            - Demand[b,t];

    s.t. Max_Inv_Limit {b in B, t in T}:
        I[b,ord(t)] <= V_max[b];

    s.t. Link_Order_Binary {d in D, b in B, t in T}:
        x0[d,b,t] + sum {l in L} x[d,b,t,l] <= S_avail[d,t] * y_skl[d,b,t];

    s.t. Min_Order_Quantity {d in D, b in B, t in T}:
        x0[d,b,t] + sum {l in L} x[d,b,t,l] >= 0.001 * y_skl[d,b,t];

    s.t. Max_Availability {d in D, t in T}:
        sum {b in B} (x0[d,b,t] + sum {l in L} x[d,b,t,l]) <= S_avail[d,t];

    s.t. Threshold_0_Max {d in D, b in B, t in T}:
        x0[d,b,t] <= Q[d,first(L)];

    s.t. Threshold_0_Min {d in D, b in B, t in T}:
        x0[d,b,t] >= Q[d,first(L)] * y_rab[d,b,t,first(L)];

    s.t. Threshold_L_Max_Normal {d in D, b in B, t in T, l in L: l <> last(L)}:
        x[d,b,t,l] <= (Q[d,next(l,L)] - Q[d,l]) * y_rab[d,b,t,l];

    s.t. Threshold_L_Max_Last {d in D, b in B, t in T, l in L: l == last(L)}:
        x[d,b,t,l] <= S_max * y_rab[d,b,t,l];

    s.t. Threshold_L_Min_Normal {d in D, b in B, t in T, l in L: l <> last(L)}:
        x[d,b,t,l] >= (Q[d,next(l,L)] - Q[d,l]) * y_rab[d,b,t,next(l,L)];
"""


def _build_ampl_data(request: OptimizationRequest) -> dict:
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

    Q: dict[tuple, float] = {}
    for dist in request.distributors:
        for dp in dist.daily_prices:
            for tier in dp.discount_tiers:
                Q.setdefault((dist.id, tier.level), tier.quantity_kg)
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
    }


def _load_ampl(ampl: AMPL, data: dict) -> None:
    ampl.eval(_AMPL_MODEL)
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


def _extract_results(ampl: AMPL, data: dict) -> OptimizationResult:
    solve_result = str(ampl.get_value("solve_result"))
    status = _SOLVE_STATUS_MAP.get(solve_result, "Not Solved")

    if status != "Optimal":
        return OptimizationResult(status=status, solver_message=solve_result)

    orders: list[OrderItem] = []
    x0_vals: dict = ampl.get_variable("x0").get_values().to_dict()
    x_vals: dict = ampl.get_variable("x").get_values().to_dict()

    for (d, b, t), val in x0_vals.items():
        if val > 1e-6:
            orders.append(
                OrderItem(
                    distributor_id=str(d),
                    building_id=str(b),
                    day=int(t),
                    threshold_level=0,
                    quantity_kg=round(float(val), 3),
                )
            )

    for (d, b, t, lvl), val in x_vals.items():
        if val > 1e-6:
            orders.append(
                OrderItem(
                    distributor_id=str(d),
                    building_id=str(b),
                    day=int(t),
                    threshold_level=int(lvl),
                    quantity_kg=round(float(val), 3),
                )
            )

    inventory_levels: list[InventoryLevel] = []
    I_vals: dict = ampl.get_variable("I").get_values().to_dict()
    for (b, t), val in I_vals.items():
        if int(t) > 0:  # skip t=0 (initial state stored separately)
            inventory_levels.append(
                InventoryLevel(
                    building_id=str(b),
                    day=int(t),
                    level_kg=round(float(val), 3),
                )
            )

    total_cost = float(ampl.get_objective("Total_Cost").value())

    purchase_base = 0.0
    purchase_actual = 0.0
    fixed_delivery = 0.0

    P0 = data["P0"]
    P = data["P"]
    C_fix = data["C_fix"]

    for (d, b, t), val in x0_vals.items():
        if val > 1e-6:
            p0 = P0.get((d, t), 0.0)
            purchase_base += p0 * val
            purchase_actual += p0 * val

    for (d, b, t, lvl), val in x_vals.items():
        if val > 1e-6:
            p0 = P0.get((d, t), 0.0)
            p_disc = P.get((d, t, lvl), p0)
            purchase_base += p0 * val
            purchase_actual += p_disc * val

    y_vals: dict = ampl.get_variable("y_skl").get_values().to_dict()
    for (d, b, t), val in y_vals.items():
        if val > 0.5:
            fixed_delivery += C_fix.get((d, b), 0.0)

    cost_breakdown = CostBreakdown(
        purchase_base=purchase_base,
        purchase_discount=purchase_actual - purchase_base,
        fixed_delivery=fixed_delivery,
        total=total_cost,
    )

    return OptimizationResult(
        status="Optimal",
        total_cost_pln=total_cost,
        solver_message=solve_result,
        orders=orders,
        inventory_levels=inventory_levels,
        cost_breakdown=cost_breakdown,
    )


def run_optimization(request: OptimizationRequest) -> OptimizationResult:
    data = _build_ampl_data(request)

    license_key = os.environ.get("AMPL_LICENSE_KEY")
    if license_key:
        modules.activate(license_key)

    ampl = AMPL()
    try:
        _load_ampl(ampl, data)
        ampl.set_option("solver", "highs")
        ampl.set_option("highs_options", "mip_rel_gap=1e-6 mip_abs_gap=1e-6 threads=1")
        ampl.solve()
        return _extract_results(ampl, data)
    finally:
        ampl.close()
