import { useState, useEffect } from 'react'
import {
  Card, Text, Button, Badge, Metric, Flex,
  Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell,
  Select, SelectItem, TextInput, NumberInput,
} from '@tremor/react'
import { api } from '../api/client'
import type { BuildingResponse, DistributorResponse, OptimizationResponse } from '../api/api'

function avgDemand(b: BuildingResponse): number {
  if (!b.daily_demand?.length) return 0
  return +(b.daily_demand.reduce((s, d) => s + (d.demand_kg ?? 0), 0) / b.daily_demand.length).toFixed(1)
}

export default function Optimization() {
  const [distributors, setDistributors] = useState<DistributorResponse[]>([])
  const [buildings, setBuildings] = useState<BuildingResponse[]>([])
  const [selectedDist, setSelectedDist] = useState<Set<string>>(new Set())
  const [selectedBuild, setSelectedBuild] = useState<Set<string>>(new Set())
  const [scenarioName, setScenarioName] = useState('')
  const [horizon, setHorizon] = useState('14')
  const [alpha, setAlpha] = useState<number>(0.05)
  const [running, setRunning] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [result, setResult] = useState<OptimizationResponse | null>(null)
  const [error, setError] = useState('')
  const [confirmed, setConfirmed] = useState(false)

  useEffect(() => {
    Promise.all([
      api.distributors.listDistributors(),
      api.buildings.listBuildings(),
    ]).then(([distRes, buildRes]) => {
      setDistributors(distRes.data)
      setSelectedDist(new Set(distRes.data.map(d => d.id!).filter(Boolean)))
      setBuildings(buildRes.data)
      setSelectedBuild(new Set(buildRes.data.map(b => b.id!).filter(Boolean)))
    }).catch(console.error)
  }, [])

  const toggle = (set: Set<string>, id: string) => {
    const s = new Set(set)
    s.has(id) ? s.delete(id) : s.add(id)
    return s
  }

  const handleRun = async () => {
    setRunning(true)
    setError('')
    setResult(null)
    setConfirmed(false)
    try {
      const res = await api.optimization.runOptimization({
        name: scenarioName || `Scenario ${new Date().toLocaleDateString()}`,
        planning_horizon_days: parseInt(horizon),
        distributor_ids: [...selectedDist],
        building_ids: [...selectedBuild],
        decay_rate: alpha,
      })
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Optimization failed')
    } finally {
      setRunning(false)
    }
  }

  const handleConfirm = async () => {
    if (!result?.result_id) return
    setConfirming(true)
    try {
      await api.orders.confirmOrders({ result_id: result.result_id })
      setConfirmed(true)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed to confirm order')
    } finally {
      setConfirming(false)
    }
  }

  const distName = (id?: string) =>
    distributors.find(d => d.id === id)?.username ?? id?.slice(0, 8) ?? '—'
  const buildName = (id?: string) =>
    buildings.find(b => b.id === id)?.name ?? id?.slice(0, 8) ?? '—'

  const canRun = selectedDist.size > 0 && selectedBuild.size > 0

  return (
    <div className="max-w-5xl">
      <div className="mb-7">
        <h1 className="text-xl font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
          Optimization
        </h1>
        <p className="text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle mt-0.5">
          Configure a scenario and run the AMPL solver
        </p>
      </div>

      <Card className="mb-5">
        <p className="text-sm font-medium text-tremor-content-emphasis dark:text-dark-tremor-content-emphasis mb-4">
          New scenario
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">
              Scenario name
            </label>
            <TextInput
              placeholder="e.g. May 2024 – week 1"
              value={scenarioName}
              onChange={e => setScenarioName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">
                Planning horizon (T)
              </label>
              <Select value={horizon} onValueChange={setHorizon}>
                <SelectItem value="7">7 days</SelectItem>
                <SelectItem value="14">14 days</SelectItem>
                <SelectItem value="21">21 days</SelectItem>
                <SelectItem value="30">30 days</SelectItem>
              </Select>
            </div>

            <div>
              <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">
                Daily spoilage rate (α)
              </label>
              <NumberInput
                value={alpha}
                onValueChange={v => setAlpha(v ?? 0.05)}
                min={0} max={1} step={0.01}
                placeholder="0.05"
              />
              <p className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle mt-1">
                fraction of inventory lost per day (e.g. 0.05 = 5%)
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-2">
                Distributors (D)
              </label>
              <div className="space-y-2">
                {distributors.map(d => {
                  const basePrice = d.daily_prices?.[0]?.base_price
                  const leadTime = d.delivery_params?.[0]?.lead_time_days
                  return (
                    <label key={d.id} className="flex items-center gap-2 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={selectedDist.has(d.id!)}
                        onChange={() => setSelectedDist(toggle(selectedDist, d.id!))}
                        className="rounded border-gray-300 text-blue-600"
                      />
                      <span className="text-sm text-tremor-content-strong dark:text-dark-tremor-content-strong">
                        {d.username}
                      </span>
                      <span className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                        {basePrice != null ? `${basePrice} PLN/kg` : ''}
                        {leadTime != null ? ` · LT ${leadTime}d` : ''}
                      </span>
                    </label>
                  )
                })}
              </div>
            </div>

            <div>
              <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-2">
                Buildings (B)
              </label>
              <div className="space-y-2">
                {buildings.map(b => (
                  <label key={b.id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedBuild.has(b.id!)}
                      onChange={() => setSelectedBuild(toggle(selectedBuild, b.id!))}
                      className="rounded border-gray-300 text-blue-600"
                    />
                    <span className="text-sm text-tremor-content-strong dark:text-dark-tremor-content-strong">
                      {b.name}
                    </span>
                    <span className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                      {avgDemand(b)} kg/day
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-1 flex items-center gap-3">
            <Button onClick={handleRun} loading={running} disabled={running || !canRun}>
              {running ? 'Solver running...' : 'Run optimization'}
            </Button>
            {!canRun && (
              <Text className="text-xs text-red-500">
                Select at least one distributor and one building
              </Text>
            )}
            {error && <Text className="text-xs text-red-500">{error}</Text>}
          </div>
        </div>
      </Card>

      {result && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-5">
            <Card>
              <Text>Total cost</Text>
              <Metric>{(result.total_cost_pln ?? 0).toLocaleString('en-US')} PLN</Metric>
              <Badge color={result.status === 'Optimal' ? 'green' : 'red'} size="xs" className="mt-2">
                {result.status}
              </Badge>
            </Card>
            <Card>
              <Text>Purchase (after discounts)</Text>
              <Metric>
                {(
                  (result.cost_breakdown?.purchase_base ?? 0) +
                  (result.cost_breakdown?.purchase_discount ?? 0)
                ).toLocaleString('en-US')} PLN
              </Metric>
              {(result.cost_breakdown?.purchase_discount ?? 0) !== 0 && (
                <Text className="text-xs text-green-600 mt-1">
                  −{Math.abs(result.cost_breakdown!.purchase_discount!).toLocaleString('en-US')} PLN savings
                </Text>
              )}
            </Card>
            <Card>
              <Text>Delivery costs (C_fix)</Text>
              <Metric>
                {(result.cost_breakdown?.fixed_delivery ?? 0).toLocaleString('en-US')} PLN
              </Metric>
              <Text className="text-xs mt-1">{result.orders?.length ?? 0} deliveries total</Text>
            </Card>
          </div>

          <Card>
            <Flex className="mb-4">
              <p className="text-sm font-medium text-tremor-content-emphasis dark:text-dark-tremor-content-emphasis">
                Order schedule
              </p>
              {confirmed ? (
                <Badge color="green">Confirmed</Badge>
              ) : (
                <Button
                  size="xs"
                  color="green"
                  onClick={handleConfirm}
                  loading={confirming}
                  disabled={confirming || result.status !== 'Optimal'}
                >
                  Confirm schedule
                </Button>
              )}
            </Flex>
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Day (t)</TableHeaderCell>
                  <TableHeaderCell>Distributor (d)</TableHeaderCell>
                  <TableHeaderCell>Building (b)</TableHeaderCell>
                  <TableHeaderCell>Quantity x [kg]</TableHeaderCell>
                  <TableHeaderCell>Tier</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {result.orders?.map((o, i) => (
                  <TableRow key={i}>
                    <TableCell><Badge color="blue" size="xs">t={o.day}</Badge></TableCell>
                    <TableCell><Text>{distName(o.distributor_id)}</Text></TableCell>
                    <TableCell><Text>{buildName(o.building_id)}</Text></TableCell>
                    <TableCell><Text>{o.quantity_kg} kg</Text></TableCell>
                    <TableCell>
                      <Text>{o.threshold_level === 0 ? 'base' : `tier ${o.threshold_level}`}</Text>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {result.solver_message && (
              <Text className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle mt-3">
                Solver: {result.solver_message}
              </Text>
            )}
          </Card>
        </>
      )}
    </div>
  )
}
