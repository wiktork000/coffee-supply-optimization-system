import { useState, useEffect } from 'react'
import {
  Card, Text, Badge, Button, ProgressBar, Flex,
  Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell,
  TextInput, NumberInput,
} from '@tremor/react'
import { api } from '../api/client'
import type { BuildingResponse } from '../api/api'
import Modal from '../components/Modal'

function avgDemand(b: BuildingResponse): number {
  if (!b.daily_demand?.length) return 0
  return +(b.daily_demand.reduce((s, d) => s + (d.demand_kg ?? 0), 0) / b.daily_demand.length).toFixed(1)
}

function fillPct(b: BuildingResponse): number {
  if (!b.max_capacity_kg) return 0
  return Math.round(((b.current_inventory_kg ?? 0) / b.max_capacity_kg) * 100)
}

type ModalState =
  | { type: 'none' }
  | { type: 'create' }
  | { type: 'edit'; b: BuildingResponse }
  | { type: 'inventory'; b: BuildingResponse }
  | { type: 'delete'; b: BuildingResponse }

export default function Buildings() {
  const [buildings, setBuildings] = useState<BuildingResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<ModalState>({ type: 'none' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const [name, setName] = useState('')
  const [location, setLocation] = useState('')
  const [maxCap, setMaxCap] = useState<number>(100)
  const [initInv, setInitInv] = useState<number>(0)
  const [dailyUsage, setDailyUsage] = useState<number>(0)
  const [currentKg, setCurrentKg] = useState<number>(0)

  const load = () => {
    setLoading(true)
    api.buildings.listBuildings()
      .then(r => setBuildings(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  function openCreate() {
    setName(''); setLocation(''); setMaxCap(100); setInitInv(0); setDailyUsage(0)
    setError('')
    setModal({ type: 'create' })
  }

  function openEdit(b: BuildingResponse) {
    setName(b.name ?? '')
    setLocation(b.location ?? '')
    setMaxCap(b.max_capacity_kg ?? 0)
    setDailyUsage(avgDemand(b))
    setError('')
    setModal({ type: 'edit', b })
  }

  function openInventory(b: BuildingResponse) {
    setCurrentKg(b.current_inventory_kg ?? 0)
    setError('')
    setModal({ type: 'inventory', b })
  }

  function close() { setModal({ type: 'none' }); setError('') }

  async function handleSave() {
    setSaving(true); setError('')
    const daily_demand = Array.from({ length: 7 }, (_, i) => ({ day: i + 1, demand_kg: dailyUsage }))
    const body = {
      name,
      location: location.trim() || null,
      max_capacity_kg: maxCap,
      initial_inventory_kg: modal.type === 'create' ? initInv : undefined,
      daily_demand,
    }
    try {
      if (modal.type === 'create') await api.buildings.createBuilding(body)
      else if (modal.type === 'edit') await api.buildings.updateBuilding(modal.b.id!, body)
      load(); close()
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Save failed')
    } finally { setSaving(false) }
  }

  async function handleInventory() {
    if (modal.type !== 'inventory') return
    setSaving(true); setError('')
    try {
      await api.inventory.updateInventory(modal.b.id!, { current_kg: currentKg })
      load(); close()
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Update failed')
    } finally { setSaving(false) }
  }

  async function handleDelete() {
    if (modal.type !== 'delete') return
    setSaving(true)
    try {
      await api.buildings.deleteBuilding(modal.b.id!)
      load(); close()
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Delete failed')
    } finally { setSaving(false) }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
            Buildings
          </h1>
          <p className="text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle mt-0.5">
            Delivery locations and stock levels
          </p>
        </div>
        <Button size="sm" onClick={openCreate}>Add building</Button>
      </div>

      <Card>
        {loading ? (
          <Text>Loading…</Text>
        ) : buildings.length === 0 ? (
          <Text className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
            No buildings yet. Add one to get started.
          </Text>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Building</TableHeaderCell>
                <TableHeaderCell>Location</TableHeaderCell>
                <TableHeaderCell>Stock</TableHeaderCell>
                <TableHeaderCell>Daily usage</TableHeaderCell>
                <TableHeaderCell>Stock lasts</TableHeaderCell>
                <TableHeaderCell>Actions</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {buildings.map(b => {
                const avg = avgDemand(b)
                const fill = fillPct(b)
                const daysLeft = avg > 0 ? Math.floor((b.current_inventory_kg ?? 0) / avg) : null
                return (
                  <TableRow key={b.id}>
                    <TableCell>
                      <Text className="font-medium">{b.name}</Text>
                    </TableCell>
                    <TableCell>
                      <Text className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                        {b.location ?? '—'}
                      </Text>
                    </TableCell>
                    <TableCell className="w-44">
                      <Flex className="mb-1">
                        <Text className="text-xs">{(b.current_inventory_kg ?? 0).toFixed(1)} kg</Text>
                        <Text className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                          {b.max_capacity_kg} kg max
                        </Text>
                      </Flex>
                      <ProgressBar value={fill} color={fill < 25 ? 'red' : fill < 50 ? 'yellow' : 'blue'} />
                    </TableCell>
                    <TableCell>
                      <Text>{avg} kg/day</Text>
                    </TableCell>
                    <TableCell>
                      {daysLeft === null ? (
                        <Text className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">—</Text>
                      ) : (
                        <Badge color={daysLeft <= 3 ? 'red' : daysLeft <= 7 ? 'yellow' : 'green'}>
                          ~{daysLeft}d
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button size="xs" variant="secondary" onClick={() => openEdit(b)}>Edit</Button>
                        <Button size="xs" variant="secondary" onClick={() => openInventory(b)}>Inventory</Button>
                        <Button size="xs" variant="secondary" color="red" onClick={() => setModal({ type: 'delete', b })}>
                          Delete
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        )}
      </Card>

      {(modal.type === 'create' || modal.type === 'edit') && (
        <Modal
          title={modal.type === 'create' ? 'Add building' : `Edit: ${(modal as any).b?.name}`}
          onClose={close}
          maxWidth="max-w-md"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">Name *</label>
              <TextInput value={name} onChange={e => setName(e.target.value)}/>
            </div>
            <div>
              <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">Location</label>
              <TextInput
                value={location}
                onChange={e => setLocation(e.target.value)}
              />
            </div>
            <div className={modal.type === 'create' ? 'grid grid-cols-2 gap-3' : ''}>
              <div>
                <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">
                  Max capacity (kg) *
                </label>
                <NumberInput value={maxCap} onValueChange={v => setMaxCap(v ?? 0)} min={0} />
              </div>
              {modal.type === 'create' && (
                <div>
                  <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">
                    Initial inventory (kg)
                  </label>
                  <NumberInput value={initInv} onValueChange={v => setInitInv(v ?? 0)} min={0} />
                </div>
              )}
            </div>
            <div>
              <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">
                Daily coffee usage (kg/day)
              </label>
              <NumberInput
                value={dailyUsage}
                onValueChange={v => setDailyUsage(v ?? 0)}
                min={0}
                step={0.1}
                placeholder="e.g. 8"
              />
            </div>

            {error && <p className="text-sm text-red-500">{error}</p>}

            <div className="flex gap-2 pt-2 border-t border-tremor-border dark:border-dark-tremor-border">
              <Button onClick={handleSave} loading={saving} disabled={!name.trim() || maxCap <= 0}>
                {modal.type === 'create' ? 'Create' : 'Save changes'}
              </Button>
              <Button variant="secondary" onClick={close}>Cancel</Button>
            </div>
          </div>
        </Modal>
      )}

      {modal.type === 'inventory' && (
        <Modal title={`Update inventory: ${modal.b.name}`} onClose={close} maxWidth="max-w-sm">
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">
                Current inventory (kg)
                <span className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle ml-1">
                  max {modal.b.max_capacity_kg} kg
                </span>
              </label>
              <NumberInput
                value={currentKg}
                onValueChange={v => setCurrentKg(v ?? 0)}
                min={0}
                max={modal.b.max_capacity_kg}
              />
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <div className="flex gap-2 pt-2 border-t border-tremor-border dark:border-dark-tremor-border">
              <Button onClick={handleInventory} loading={saving}>Update</Button>
              <Button variant="secondary" onClick={close}>Cancel</Button>
            </div>
          </div>
        </Modal>
      )}

      {modal.type === 'delete' && (
        <Modal title="Delete building" onClose={close} maxWidth="max-w-sm">
          <p className="text-sm text-tremor-content dark:text-dark-tremor-content mb-4">
            Are you sure you want to delete <strong>{modal.b.name}</strong>? This cannot be undone.
          </p>
          {error && <p className="text-sm text-red-500 mb-3">{error}</p>}
          <div className="flex gap-2">
            <Button color="red" onClick={handleDelete} loading={saving}>Delete</Button>
            <Button variant="secondary" onClick={close}>Cancel</Button>
          </div>
        </Modal>
      )}
    </div>
  )
}
