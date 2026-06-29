import { useState, useEffect } from "react";
import {
    Card,
    Text,
    Badge,
    Button,
    Table,
    TableHead,
    TableRow,
    TableHeaderCell,
    TableBody,
    TableCell,
    TextInput,
} from "@tremor/react";
import { api } from "../api/client";
import type { OrderRecord, CorrectionResponse, BuildingResponse, DistributorResponse } from "../api/api";
import Modal from "../components/Modal";

const STATUSES = ["confirmed", "pending", "cancelled"] as const;
type OrderStatus = (typeof STATUSES)[number];

const statusConfig: Record<
    OrderStatus,
    { label: string; color: "blue" | "yellow" | "gray" }
> = {
    confirmed: { label: "Confirmed", color: "blue" },
    pending: { label: "Pending", color: "yellow" },
    cancelled: { label: "Cancelled", color: "gray" },
};

type ModalState =
    | { type: "none" }
    | { type: "viewDetails"; order: OrderRecord }
    | { type: "changeStatus"; order: OrderRecord; selected: OrderStatus }
    | { type: "runCorrection"; order: OrderRecord; name: string }
    | {
          type: "correctionResult";
          order: OrderRecord;
          result: CorrectionResponse;
          confirming: boolean;
          confirmed: boolean;
      };

export default function Orders() {
    const [orders, setOrders] = useState<OrderRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [modal, setModal] = useState<ModalState>({ type: "none" });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [buildingMap, setBuildingMap] = useState<Record<string, string>>({});
    const [distributorMap, setDistributorMap] = useState<Record<string, string>>({});

    const load = () => {
        api.orders
            .listOrders()
            .then((res) => {
                const sorted = [...res.data].sort(
                    (a, b) =>
                        new Date(b.created_at).getTime() -
                        new Date(a.created_at).getTime(),
                );
                setOrders(sorted);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        load();
        api.buildings.listBuildings()
            .then((res) => {
                const map: Record<string, string> = {};
                (res.data as BuildingResponse[]).forEach((b) => { map[b.id] = b.name; });
                setBuildingMap(map);
            })
            .catch(console.error);
        api.distributors.listDistributors()
            .then((res) => {
                const map: Record<string, string> = {};
                (res.data as DistributorResponse[]).forEach((d) => { map[d.id] = d.username; });
                setDistributorMap(map);
            })
            .catch(console.error);
    }, []);

    function openStatusModal(order: OrderRecord) {
        setError("");
        setModal({
            type: "changeStatus",
            order,
            selected: (order.status ?? "confirmed") as OrderStatus,
        });
    }

    function openDetailsModal(order: OrderRecord) {
        setError("");
        setModal({ type: "viewDetails", order });
    }

    function openCorrectionModal(order: OrderRecord) {
        setError("");
        setModal({
            type: "runCorrection",
            order,
            name: `Correction ${new Date().toLocaleDateString("en-US")}`,
        });
    }

    function close() {
        setModal({ type: "none" });
        setError("");
    }

    async function handleStatusSave() {
        if (modal.type !== "changeStatus") return;
        setSaving(true);
        setError("");
        try {
            await api.orders.updateOrderStatus(modal.order.id!, {
                status: modal.selected,
            });
            load();
            close();
        } catch (e: any) {
            setError(e?.response?.data?.detail ?? "Update failed");
        } finally {
            setSaving(false);
        }
    }

    async function handleCorrectionSubmit() {
        if (modal.type !== "runCorrection") return;
        setSaving(true);
        setError("");
        try {
            const res = await api.optimization.runCorrection({
                name: modal.name,
                previous_result_id: modal.order.result_id!,
            });
            setModal({
                type: "correctionResult",
                order: modal.order,
                result: res.data,
                confirming: false,
                confirmed: false,
            });
        } catch (e: any) {
            setError(
                e?.response?.data?.detail ?? "Correction optimization failed",
            );
        } finally {
            setSaving(false);
        }
    }

    async function handleConfirmCorrection() {
        if (modal.type !== "correctionResult") return;
        setModal({ ...modal, confirming: true });
        setError("");
        try {
            await api.orders.confirmOrders({
                result_id: modal.result.result_id,
            });
            setModal({ ...modal, confirming: false, confirmed: true });
            load();
        } catch (e: any) {
            setError(e?.response?.data?.detail ?? "Confirmation failed");
            setModal({ ...modal, confirming: false });
        }
    }

    return (
        <div>
            <div className="mb-6">
                <h1 className="text-xl font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
                    Order history
                </h1>
                <p className="text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle mt-0.5">
                    Registry of confirmed order schedules
                </p>
            </div>

            <Card>
                {loading ? (
                    <Text>Loading...</Text>
                ) : orders.length === 0 ? (
                    <Text className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                        No orders yet.
                    </Text>
                ) : (
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableHeaderCell>Order ID</TableHeaderCell>
                                <TableHeaderCell>Scenario</TableHeaderCell>
                                <TableHeaderCell>Items</TableHeaderCell>
                                <TableHeaderCell>Total cost</TableHeaderCell>
                                <TableHeaderCell>Date</TableHeaderCell>
                                <TableHeaderCell>Confirmed by</TableHeaderCell>
                                <TableHeaderCell>Status</TableHeaderCell>
                                <TableHeaderCell>Actions</TableHeaderCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {orders.map((o) => {
                                const s =
                                    statusConfig[
                                        (o.status ?? "confirmed") as OrderStatus
                                    ] ?? statusConfig["confirmed"];
                                return (
                                    <TableRow key={o.id}>
                                        <TableCell>
                                            <Text className="font-mono text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                                {o.id?.slice(0, 8)}…
                                            </Text>
                                        </TableCell>
                                        <TableCell>
                                            <Text className="font-mono text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                                {o.scenario_id?.slice(0, 8)}…
                                            </Text>
                                        </TableCell>
                                        <TableCell>
                                            <Text>
                                                {o.orders?.length ?? 0}{" "}
                                                deliveries
                                            </Text>
                                        </TableCell>
                                        <TableCell>
                                            <Text className="font-semibold">
                                                {(
                                                    o.total_cost_pln ?? 0
                                                ).toLocaleString("en-US")}{" "}
                                                PLN
                                            </Text>
                                        </TableCell>
                                        <TableCell>
                                            <Text className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                                {o.created_at
                                                    ? new Date(
                                                          o.created_at,
                                                      ).toLocaleDateString(
                                                          "en-US",
                                                      )
                                                    : "—"}
                                            </Text>
                                        </TableCell>
                                        <TableCell>
                                            <Text className="font-mono text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                                {o.confirmed_by?.slice(0, 8) ??
                                                    "—"}
                                            </Text>
                                        </TableCell>
                                        <TableCell>
                                            <Badge color={s.color}>
                                                {s.label}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex gap-2">
                                                <Button
                                                    size="xs"
                                                    variant="secondary"
                                                    onClick={() =>
                                                        openDetailsModal(o)
                                                    }
                                                >
                                                    View details
                                                </Button>
                                                <Button
                                                    size="xs"
                                                    variant="secondary"
                                                    onClick={() =>
                                                        openStatusModal(o)
                                                    }
                                                >
                                                    Change status
                                                </Button>
                                                <Button
                                                    size="xs"
                                                    variant="secondary"
                                                    onClick={() =>
                                                        openCorrectionModal(o)
                                                    }
                                                >
                                                    Run correction
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                )}
            </Card>

            {modal.type === "viewDetails" && (
                <Modal
                    title="Order details"
                    onClose={close}
                    maxWidth="max-w-3xl"
                >
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                            <div>
                                <span className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">Order ID</span>
                                <p className="font-mono text-xs text-tremor-content-strong dark:text-dark-tremor-content-strong mt-0.5">{modal.order.id}</p>
                            </div>
                            <div>
                                <span className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">Scenario ID</span>
                                <p className="font-mono text-xs text-tremor-content-strong dark:text-dark-tremor-content-strong mt-0.5">{modal.order.scenario_id}</p>
                            </div>
                            <div>
                                <span className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">Total cost</span>
                                <p className="font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong mt-0.5">
                                    {(modal.order.total_cost_pln ?? 0).toLocaleString("en-US")} PLN
                                </p>
                            </div>
                            <div>
                                <span className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">Date</span>
                                <p className="text-tremor-content-strong dark:text-dark-tremor-content-strong mt-0.5">
                                    {modal.order.created_at
                                        ? new Date(modal.order.created_at).toLocaleString("en-US")
                                        : "—"}
                                </p>
                            </div>
                            <div>
                                <span className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">Status</span>
                                <p className="mt-0.5">
                                    <Badge color={statusConfig[(modal.order.status ?? "confirmed") as OrderStatus]?.color ?? "blue"}>
                                        {statusConfig[(modal.order.status ?? "confirmed") as OrderStatus]?.label ?? modal.order.status}
                                    </Badge>
                                </p>
                            </div>
                            <div>
                                <span className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">Confirmed by</span>
                                <p className="font-mono text-xs text-tremor-content-strong dark:text-dark-tremor-content-strong mt-0.5">
                                    {modal.order.confirmed_by ?? "—"}
                                </p>
                            </div>
                        </div>

                        <div>
                            <p className="text-sm font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong mb-2">
                                Deliveries ({modal.order.orders?.length ?? 0})
                            </p>
                            {(modal.order.orders?.length ?? 0) === 0 ? (
                                <p className="text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle">No deliveries.</p>
                            ) : (
                                <div className="overflow-auto max-h-72 rounded-tremor-default border border-tremor-border dark:border-dark-tremor-border">
                                    <Table>
                                        <TableHead>
                                            <TableRow>
                                                <TableHeaderCell>Day</TableHeaderCell>
                                                <TableHeaderCell>Distributor</TableHeaderCell>
                                                <TableHeaderCell>Building</TableHeaderCell>
                                                <TableHeaderCell>Tier</TableHeaderCell>
                                                <TableHeaderCell>Qty (kg)</TableHeaderCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {modal.order.orders.map((item, i) => (
                                                <TableRow key={i}>
                                                    <TableCell><Text>{item.day}</Text></TableCell>
                                                    <TableCell>
                                                        <Text>
                                                            {distributorMap[item.distributor_id] ?? item.distributor_id.slice(0, 8) + "…"}
                                                        </Text>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Text>
                                                            {buildingMap[item.building_id] ?? item.building_id.slice(0, 8) + "…"}
                                                        </Text>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Text>
                                                            {item.threshold_level === 0 ? "base" : `T${item.threshold_level}`}
                                                        </Text>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Text className="font-semibold">
                                                            {item.quantity_kg.toFixed(2)}
                                                        </Text>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            )}
                        </div>

                        <div className="flex pt-2 border-t border-tremor-border dark:border-dark-tremor-border">
                            <Button variant="secondary" onClick={close}>Close</Button>
                        </div>
                    </div>
                </Modal>
            )}

            {modal.type === "changeStatus" && (
                <Modal
                    title="Change order status"
                    onClose={close}
                    maxWidth="max-w-sm"
                >
                    <div className="space-y-4">
                        <p className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle font-mono">
                            Order {modal.order.id?.slice(0, 8)}…
                        </p>
                        <div className="flex gap-2">
                            {STATUSES.map((s) => {
                                const cfg = statusConfig[s];
                                const active = modal.selected === s;
                                return (
                                    <button
                                        key={s}
                                        onClick={() =>
                                            setModal({ ...modal, selected: s })
                                        }
                                        className={`flex-1 py-2 px-3 rounded-tremor-default border text-sm font-medium transition-colors ${
                                            active
                                                ? "bg-tremor-brand text-white border-tremor-brand dark:bg-dark-tremor-brand dark:border-dark-tremor-brand"
                                                : "border-tremor-border dark:border-dark-tremor-border text-tremor-content dark:text-dark-tremor-content hover:bg-tremor-background-muted dark:hover:bg-dark-tremor-background"
                                        }`}
                                    >
                                        {cfg.label}
                                    </button>
                                );
                            })}
                        </div>
                        {error && (
                            <p className="text-sm text-red-500">{error}</p>
                        )}
                        <div className="flex gap-2 pt-2 border-t border-tremor-border dark:border-dark-tremor-border">
                            <Button
                                onClick={handleStatusSave}
                                loading={saving}
                                disabled={modal.selected === modal.order.status}
                            >
                                Save
                            </Button>
                            <Button variant="secondary" onClick={close}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                </Modal>
            )}

            {modal.type === "runCorrection" && (
                <Modal
                    title="Run correction optimization"
                    onClose={close}
                    maxWidth="max-w-md"
                >
                    <div className="space-y-4">
                        <div className="p-3 rounded-tremor-default bg-tremor-background-muted dark:bg-dark-tremor-background-muted text-xs font-mono space-y-1">
                            <p className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                Base order:{" "}
                                <span className="text-tremor-content-strong dark:text-dark-tremor-content-strong">
                                    {modal.order.id?.slice(0, 8)}…
                                </span>
                            </p>
                            <p className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                Cost:{" "}
                                <span className="text-tremor-content-strong dark:text-dark-tremor-content-strong">
                                    {(
                                        modal.order.total_cost_pln ?? 0
                                    ).toLocaleString("en-US")}{" "}
                                    PLN
                                </span>
                            </p>
                            <p className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                Items:{" "}
                                <span className="text-tremor-content-strong dark:text-dark-tremor-content-strong">
                                    {modal.order.orders?.length ?? 0} deliveries
                                </span>
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong mb-1">
                                Correction name
                            </label>
                            <TextInput
                                value={modal.name}
                                onValueChange={(v) =>
                                    setModal({ ...modal, name: v })
                                }
                                placeholder="e.g. Correction 2024-01-15"
                            />
                        </div>

                        <p className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                            The optimizer will recalculate the plan using
                            current correction costs and limits configured for
                            each distributor-building pair.
                        </p>

                        {error && (
                            <p className="text-sm text-red-500">{error}</p>
                        )}
                        <div className="flex gap-2 pt-2 border-t border-tremor-border dark:border-dark-tremor-border">
                            <Button
                                onClick={handleCorrectionSubmit}
                                loading={saving}
                                disabled={!modal.name.trim()}
                            >
                                Run optimizer
                            </Button>
                            <Button variant="secondary" onClick={close}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                </Modal>
            )}

            {modal.type === "correctionResult" && (
                <Modal
                    title="Correction result"
                    onClose={close}
                    maxWidth="max-w-2xl"
                >
                    <div className="space-y-5">
                        <div className="flex items-center gap-4 flex-wrap">
                            <Badge
                                color={
                                    modal.result.status === "Optimal"
                                        ? "green"
                                        : "red"
                                }
                            >
                                {modal.result.status}
                            </Badge>
                            {modal.result.total_cost_pln != null && (
                                <span className="text-lg font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
                                    {modal.result.total_cost_pln.toLocaleString(
                                        "en-US",
                                    )}{" "}
                                    PLN
                                </span>
                            )}
                            <span className="text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                {modal.result.orders.length} deliveries ·{" "}
                                {modal.result.corrections.length} corrections
                            </span>
                        </div>

                        {modal.result.corrections.length > 0 ? (
                            <div>
                                <p className="text-sm font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong mb-2">
                                    Applied corrections
                                </p>
                                <div className="overflow-auto max-h-64 rounded-tremor-default border border-tremor-border dark:border-dark-tremor-border">
                                    <Table>
                                        <TableHead>
                                            <TableRow>
                                                <TableHeaderCell>
                                                    Day
                                                </TableHeaderCell>
                                                <TableHeaderCell>
                                                    Distributor
                                                </TableHeaderCell>
                                                <TableHeaderCell>
                                                    Building
                                                </TableHeaderCell>
                                                <TableHeaderCell>
                                                    Tier
                                                </TableHeaderCell>
                                                <TableHeaderCell>
                                                    Type
                                                </TableHeaderCell>
                                                <TableHeaderCell>
                                                    Qty (kg)
                                                </TableHeaderCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {modal.result.corrections.map(
                                                (c, i) => (
                                                    <TableRow key={i}>
                                                        <TableCell>
                                                            <Text>{c.day}</Text>
                                                        </TableCell>
                                                        <TableCell>
                                                            <Text className="font-mono text-xs">
                                                                {c.distributor_id.slice(
                                                                    0,
                                                                    8,
                                                                )}
                                                                …
                                                            </Text>
                                                        </TableCell>
                                                        <TableCell>
                                                            <Text className="font-mono text-xs">
                                                                {c.building_id.slice(
                                                                    0,
                                                                    8,
                                                                )}
                                                                …
                                                            </Text>
                                                        </TableCell>
                                                        <TableCell>
                                                            <Text>
                                                                {c.threshold_level ===
                                                                0
                                                                    ? "base"
                                                                    : `T${c.threshold_level}`}
                                                            </Text>
                                                        </TableCell>
                                                        <TableCell>
                                                            <Badge
                                                                color={
                                                                    c.type ===
                                                                    "increase"
                                                                        ? "green"
                                                                        : "red"
                                                                }
                                                            >
                                                                {c.type}
                                                            </Badge>
                                                        </TableCell>
                                                        <TableCell>
                                                            <Text className="font-semibold">
                                                                {c.quantity_kg.toFixed(
                                                                    2,
                                                                )}
                                                            </Text>
                                                        </TableCell>
                                                    </TableRow>
                                                ),
                                            )}
                                        </TableBody>
                                    </Table>
                                </div>
                            </div>
                        ) : (
                            <p className="text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                No corrections needed — the current plan is
                                already optimal.
                            </p>
                        )}

                        {modal.result.solver_message && (
                            <p className="text-xs font-mono text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                Solver: {modal.result.solver_message}
                            </p>
                        )}

                        {error && (
                            <p className="text-sm text-red-500">{error}</p>
                        )}

                        <div className="flex gap-2 pt-2 border-t border-tremor-border dark:border-dark-tremor-border">
                            {modal.result.status === "Optimal" &&
                                !modal.confirmed && (
                                    <Button
                                        onClick={handleConfirmCorrection}
                                        loading={modal.confirming}
                                    >
                                        Accept and update order
                                    </Button>
                                )}
                            {modal.confirmed && (
                                <Badge color="green">Order updated</Badge>
                            )}
                            <Button variant="secondary" onClick={close}>
                                Close
                            </Button>
                        </div>
                    </div>
                </Modal>
            )}
        </div>
    );
}
