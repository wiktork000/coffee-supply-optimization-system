import { useState, useEffect } from 'react'
import { Card, Text, ProgressBar, Flex, Badge } from '@tremor/react'
import { api } from '../api/client'
import type { InventoryStatus, OrderRecord, DistributorResponse } from '../api/api'

export default function Dashboard() {
  const [inventory, setInventory] = useState<InventoryStatus[]>([])
  const [orders, setOrders] = useState<OrderRecord[]>([])
  const [distributors, setDistributors] = useState<DistributorResponse[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.inventory.getInventory(),
      api.orders.listOrders(),
      api.distributors.listDistributors(),
    ])
      .then(([invRes, ordRes, distRes]) => {
        setInventory(invRes.data)
        setOrders(ordRes.data)
        setDistributors(distRes.data)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const lowStock = inventory.filter(b => (b.fill_percent ?? 0) < 25)
  const lastOrder = orders[0] ?? null
  const totalInventory = inventory.reduce((s, b) => s + (b.current_inventory_kg ?? 0), 0)

  const statusColor: Record<string, 'blue' | 'yellow' | 'gray'> = {
    confirmed: 'blue',
    pending: 'yellow',
    cancelled: 'gray',
  }

  return (
    <div className="max-w-4xl">
      <div className="mb-7">
        <h1 className="text-xl font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
          Dashboard
        </h1>
        <p className="text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle mt-0.5">
          {new Date().toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          })}
        </p>
      </div>

      {!loading && lowStock.length > 0 && (
        <div className="mb-5 p-3 rounded-tremor-default bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900">
          <p className="text-sm text-red-700 dark:text-red-400 font-medium">
            ⚠ Low stock: {lowStock.map(b => b.building_name).join(', ')}
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 mb-5">
        <Card>
          <Text>Total inventory</Text>
          <p className="text-2xl font-bold text-tremor-content-strong dark:text-dark-tremor-content-strong mt-1">
            {loading ? '—' : `${totalInventory.toFixed(1)} kg`}
          </p>
          <Text className="text-xs mt-1">across {inventory.length} locations</Text>
        </Card>
        <Card>
          <Text>Active distributors</Text>
          <p className="text-2xl font-bold text-tremor-content-strong dark:text-dark-tremor-content-strong mt-1">
            {loading ? '—' : distributors.filter(d => d.active).length}
          </p>
          <Text className="text-xs mt-1">of {distributors.length} total</Text>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <p className="text-sm font-medium text-tremor-content-emphasis dark:text-dark-tremor-content-emphasis mb-4">
            Stock levels
          </p>
          {loading ? (
            <Text>Loading…</Text>
          ) : inventory.length === 0 ? (
            <Text className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
              No buildings yet
            </Text>
          ) : (
            <div className="space-y-3.5">
              {inventory.map(b => (
                <div key={b.building_id}>
                  <Flex className="mb-1">
                    <Text className="text-xs">{b.building_name}</Text>
                    <Text
                      className={`text-xs font-medium ${(b.fill_percent ?? 0) < 25 ? 'text-red-500' : ''}`}
                    >
                      {(b.current_inventory_kg ?? 0).toFixed(1)} kg
                    </Text>
                  </Flex>
                  <ProgressBar
                    value={b.fill_percent ?? 0}
                    color={
                      (b.fill_percent ?? 0) < 25
                        ? 'red'
                        : (b.fill_percent ?? 0) < 50
                          ? 'yellow'
                          : 'blue'
                    }
                  />
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <p className="text-sm font-medium text-tremor-content-emphasis dark:text-dark-tremor-content-emphasis mb-1">
            Last order
          </p>
          {loading ? (
            <Text>Loading…</Text>
          ) : !lastOrder ? (
            <Text className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle mt-2">
              No orders yet
            </Text>
          ) : (
            <>
              <Text className="text-xs mb-4 font-mono text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                {lastOrder.scenario_id?.slice(0, 8)}…
              </Text>
              <div className="space-y-2.5">
                <div className="flex justify-between text-sm">
                  <span className="text-tremor-content dark:text-dark-tremor-content">Deliveries</span>
                  <span className="text-tremor-content-strong dark:text-dark-tremor-content-strong font-medium">
                    {lastOrder.orders?.length ?? 0}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-tremor-content dark:text-dark-tremor-content">Total cost</span>
                  <span className="text-tremor-content-strong dark:text-dark-tremor-content-strong font-semibold">
                    {(lastOrder.total_cost_pln ?? 0).toLocaleString('en-US')} PLN
                  </span>
                </div>
                <div className="flex justify-between text-sm items-center">
                  <span className="text-tremor-content dark:text-dark-tremor-content">Status</span>
                  <Badge color={statusColor[lastOrder.status ?? ''] ?? 'gray'} size="xs">
                    {lastOrder.status ?? '—'}
                  </Badge>
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-tremor-border dark:border-dark-tremor-border">
                <Text className="text-xs">
                  {lastOrder.created_at
                    ? new Date(lastOrder.created_at).toLocaleDateString('en-US', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric',
                      })
                    : '—'}
                </Text>
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  )
}
