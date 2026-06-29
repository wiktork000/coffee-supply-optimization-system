import { useEffect, useState, type FocusEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Text, Badge, Button } from '@tremor/react'
import { useTheme } from '../context/ThemeContext'
import { api } from '../api/client'
import type { BuildingResponse } from '../api/api'
import { buildDistributorUpdatePayload } from '../utils/distributorPanelMapper'

type Tier = { threshold: number; price: number }

type DayPrice = {
  local_id: string
  day: number
  base_price: number
  availability_kg: number
  tiers: Tier[]
}

type DeliveryParam = {
  building_id: string
  building_name: string
  lead_time_days: number
  fixed_cost_pln: number
}

const fieldCls = "w-full text-sm border border-tremor-border dark:border-dark-tremor-border rounded px-2 py-1.5 bg-tremor-background dark:bg-dark-tremor-background-subtle text-tremor-content-strong dark:text-dark-tremor-content-strong focus:outline-none focus:ring-2 focus:ring-tremor-brand dark:focus:ring-dark-tremor-brand"
const labelCls = "text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle mb-1 block"
const iconBtnCls = "text-xs px-1.5 py-0.5 rounded border transition-colors"

const createLocalId = () =>
  `day-${Date.now()}-${Math.random().toString(36).slice(2)}`

const getNextWeekStart = (prices: DayPrice[]) => {
  if (prices.length === 0) {
    return 1
  }

  return Math.max(...prices.map(p => p.day)) + 1
}

const selectZeroOnFocus = (event: FocusEvent<HTMLInputElement>) => {
  if (event.currentTarget.value === '0') {
    event.currentTarget.select()
  }
}

const getApiKey = () => localStorage.getItem('dist_auth') ?? ''

export default function DistributorPanel() {
  const navigate = useNavigate()
  const { theme, toggle } = useTheme()

  const [distributorName, setDistributorName] = useState('Distributor')
  const [contactEmail, setContactEmail] = useState('')
  const [prices, setPrices] = useState<DayPrice[]>([])
  const [delivery, setDelivery] = useState<DeliveryParam[]>([])
  const [availableBuildings, setAvailableBuildings] = useState<BuildingResponse[]>([])
  const [addingDelivery, setAddingDelivery] = useState(false)
  const [newDeliveryBuildingId, setNewDeliveryBuildingId] = useState('')
  const [newDeliveryLeadTime, setNewDeliveryLeadTime] = useState(1)
  const [newDeliveryFixedCost, setNewDeliveryFixedCost] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  useEffect(() => {
    const loadDistributorData = async () => {
      const apiKey = getApiKey()

      if (!apiKey) {
        navigate('/distributor/login')
        return
      }

      setLoading(true)
      setLoadError('')

      try {
        const pricesResponse = await api.distributors.getOwnPrices({
          headers: { 'X-Api-Key': apiKey },
        })

        const data = pricesResponse.data as any

        let buildings: BuildingResponse[] = []
        try {
          const buildingsResponse = await api.distributors.getOwnAvailableBuildings({
            headers: { 'X-Api-Key': apiKey },
          })
          buildings = buildingsResponse.data
        } catch {
          
        }

        setDistributorName(data.username ?? 'Distributor')
        setContactEmail(data.contact_email ?? '')
        setAvailableBuildings(buildings)

        setPrices(
          (data.daily_prices ?? []).map((price: any, index: number) => ({
            local_id: `day-${price.day}-${index}`,
            day: price.day,
            base_price: price.base_price,
            availability_kg: price.availability_kg,
            tiers: (price.discount_tiers ?? []).map((tier: any) => ({
              threshold: tier.quantity_kg,
              price: tier.unit_price,
            })),
          })),
        )

        setDelivery(
          (data.delivery_params ?? []).map((param: any, index: number) => {
            const building = buildings.find(b => b.id === param.building_id)

            return {
              building_id: param.building_id,
              building_name: building?.name ?? `Building ${index + 1}`,
              lead_time_days: param.lead_time_days,
              fixed_cost_pln: param.fixed_cost_pln,
            }
          }),
        )
      } catch (e) {
        console.error('Distributor panel load error:', e)
        setLoadError('Could not load distributor data')
      } finally {
        setLoading(false)
      }
    }

    loadDistributorData()
  }, [navigate])

  const handleLogout = () => {
    localStorage.removeItem('dist_auth')
    navigate('/distributor/login')
  }

  const handleSave = async () => {
    const apiKey = getApiKey()

    if (!apiKey) {
      setSaveError('Missing API key. Please sign in again.')
      setSaved(false)
      return
    }

    setSaving(true)
    setSaved(false)
    setSaveError('')

    const payload = buildDistributorUpdatePayload(prices, delivery)

    try {
      await api.distributors.updateOwnPrices(payload, {
        headers: {
          'X-Api-Key': apiKey,
        },
      })

      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch {
      setSaveError('Could not save changes')
    } finally {
      setSaving(false)
    }
  }

  const updateDayField = (localId: string, field: 'base_price' | 'availability_kg', value: string) => {
    setPrices(prev => prev.map(p => p.local_id === localId ? { ...p, [field]: parseFloat(value) || 0 } : p))
  }

  const removeDay = (localId: string) => {
    setPrices(prev => prev.filter(p => p.local_id !== localId))
  }

  const addWeek = () => {
    setPrices(prev => {
      const startDay = getNextWeekStart(prev)

      const weekPrices: DayPrice[] = Array.from({ length: 7 }, (_, index) => ({
        local_id: `${createLocalId()}-${index}`,
        day: startDay + index,
        base_price: 0,
        availability_kg: 0,
        tiers: [],
      }))

      return [...prev, ...weekPrices]
    })
  }

  const updateDayNumber = (localId: string, value: string) => {
    const newDay = parseInt(value)

    if (!newDay || newDay < 1) {
      return
    }

    setPrices(prev => {
      const dayAlreadyExists = prev.some(
        p => p.local_id !== localId && p.day === newDay,
      )

      if (dayAlreadyExists) {
        return prev
      }

      return prev.map(p =>
        p.local_id === localId ? { ...p, day: newDay } : p,
      )
    })
  }

  const addTier = (localId: string) => {
    setPrices(prev => prev.map(p =>
      p.local_id === localId
        ? { ...p, tiers: [...p.tiers, { threshold: 0, price: 0 }] }
        : p,
    ))
  }

  const removeTier = (localId: string, idx: number) => {
    setPrices(prev => prev.map(p =>
      p.local_id === localId ? { ...p, tiers: p.tiers.filter((_, i) => i !== idx) } : p
    ))
  }

  const updateTier = (localId: string, idx: number, field: keyof Tier, value: string) => {
    setPrices(prev => prev.map(p =>
      p.local_id === localId
        ? { ...p, tiers: p.tiers.map((t, i) => i === idx ? { ...t, [field]: parseFloat(value) || 0 } : t) }
        : p
    ))
  }

  const updateDelivery = (buildingId: string, field: 'lead_time_days' | 'fixed_cost_pln', value: string) => {
    setDelivery(prev => prev.map(d => d.building_id === buildingId ? { ...d, [field]: parseFloat(value) || 0 } : d))
  }

  const getUnusedBuildings = () =>
    availableBuildings.filter(
      building => !delivery.some(param => param.building_id === building.id),
    )

  const openAddDelivery = () => {
    const firstAvailableBuilding = getUnusedBuildings()[0]

    if (!firstAvailableBuilding) {
      return
    }

    setNewDeliveryBuildingId(firstAvailableBuilding.id)
    setNewDeliveryLeadTime(1)
    setNewDeliveryFixedCost(0)
    setAddingDelivery(true)
  }

  const cancelAddDelivery = () => {
    setAddingDelivery(false)
    setNewDeliveryBuildingId('')
    setNewDeliveryLeadTime(1)
    setNewDeliveryFixedCost(0)
  }

  const addDelivery = () => {
    const building = availableBuildings.find(
      item => item.id === newDeliveryBuildingId,
    )

    if (!building) {
      return
    }

    setDelivery(prev => [
      ...prev,
      {
        building_id: building.id,
        building_name: building.name,
        lead_time_days: newDeliveryLeadTime,
        fixed_cost_pln: newDeliveryFixedCost,
      },
    ])

    cancelAddDelivery()
  }

  const removeDelivery = (buildingId: string) => {
    setDelivery(prev => prev.filter(param => param.building_id !== buildingId))
  }

  const sortedPrices = [...prices].sort((a, b) => a.day - b.day)
  const apiKeyForDisplay = getApiKey()
  const unusedBuildings = getUnusedBuildings()

  if (loading) {
    return (
      <div className="min-h-screen bg-tremor-background-muted dark:bg-dark-tremor-background flex items-center justify-center">
        <Text>Loading distributor data...</Text>
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="min-h-screen bg-tremor-background-muted dark:bg-dark-tremor-background flex items-center justify-center">
        <div className="text-center space-y-3">
          <Text className="text-red-500">{loadError}</Text>
          <Button variant="secondary" onClick={handleLogout}>Back to login</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-tremor-background-muted dark:bg-dark-tremor-background">
      <header className="bg-tremor-background dark:bg-dark-tremor-background-subtle border-b border-tremor-border dark:border-dark-tremor-border px-4 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-base font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
            ☕ CoffeeOps
          </span>
          <span className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle border-l border-tremor-border dark:border-dark-tremor-border pl-3 hidden sm:inline">
            Distributor Portal
          </span>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <button
            onClick={toggle}
            className="text-xs text-tremor-content dark:text-dark-tremor-content hover:text-tremor-content-strong dark:hover:text-dark-tremor-content-strong transition-colors"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <span className="text-sm text-tremor-content dark:text-dark-tremor-content hidden sm:inline">{distributorName}</span>
          <Button size="xs" variant="secondary" onClick={handleLogout}>Logout</Button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        <Card>
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-sm font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong truncate">
                {distributorName}
              </p>
              <p className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle mt-0.5">
                {contactEmail}
              </p>
            </div>
            <Badge color="green" size="xs">Active</Badge>
          </div>
          <div className="mt-3 pt-3 border-t border-tremor-border dark:border-dark-tremor-border">
            <Text className="text-xs">API Key</Text>
            <code className="text-xs text-tremor-content dark:text-dark-tremor-content bg-tremor-background-muted dark:bg-dark-tremor-background-muted px-2 py-1 rounded mt-1 block break-all">
              {apiKeyForDisplay ? `${apiKeyForDisplay.slice(0, 12)}••••••••••••` : 'No API key'}
            </code>
          </div>
        </Card>

        <section>
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-tremor-content-emphasis dark:text-dark-tremor-content-emphasis">
              Daily price list
            </p>
            <div className="flex items-center gap-2">
              {saving && <Text className="text-xs text-tremor-content-subtle">Saving...</Text>}
              {saved && <Text className="text-xs text-green-600">Saved ✓</Text>}
              {saveError && <Text className="text-xs text-red-500">{saveError}</Text>}
              <Button size="xs" variant="secondary" onClick={addWeek}>+ Add week</Button>
              <Button size="xs" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving...' : 'Save changes'}
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {sortedPrices.map(p => (
              <Card key={p.local_id} className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle shrink-0">Day</span>
                    <input
                      type="number" min="1"
                      value={p.day}
                      onChange={e => updateDayNumber(p.local_id, e.target.value)}
                      className="w-14 text-sm font-medium border border-tremor-border dark:border-dark-tremor-border rounded px-2 py-0.5 bg-tremor-background dark:bg-dark-tremor-background-subtle text-tremor-content-strong dark:text-dark-tremor-content-strong focus:outline-none focus:ring-2 focus:ring-tremor-brand"
                    />
                  </div>
                  <button
                    onClick={() => removeDay(p.local_id)}
                    className={`${iconBtnCls} border-red-200 text-red-500 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950`}
                    title="Remove day"
                  >
                    ✕
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className={labelCls}>Base price (PLN/kg)</label>
                    <input
                      type="number" step="0.1" min="0"
                      value={p.base_price}
                      onFocus={selectZeroOnFocus}
                      onChange={e => updateDayField(p.local_id, 'base_price', e.target.value)}
                      className={fieldCls}
                    />
                  </div>
                  <div>
                    <label className={labelCls}>Availability (kg)</label>
                    <input
                      type="number" min="0"
                      value={p.availability_kg}
                      onFocus={selectZeroOnFocus}
                      onChange={e => updateDayField(p.local_id, 'availability_kg', e.target.value)}
                      className={fieldCls}
                    />
                  </div>
                </div>

                <div className="border-t border-tremor-border dark:border-dark-tremor-border pt-2 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-tremor-content dark:text-dark-tremor-content">
                      Discount tiers
                    </p>
                    <button
                      onClick={() => addTier(p.local_id)}
                      className={`${iconBtnCls} border-tremor-border dark:border-dark-tremor-border text-tremor-content dark:text-dark-tremor-content hover:bg-tremor-background-muted dark:hover:bg-dark-tremor-background-muted`}
                    >
                      + tier
                    </button>
                  </div>

                  {p.tiers.length === 0 && (
                    <p className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle italic">
                      No tiers — base price applies to all quantities.
                    </p>
                  )}

                  {p.tiers.map((t, idx) => (
                    <div key={idx} className="flex items-end gap-1.5">
                      <div className="flex-1 min-w-0">
                        <label className={labelCls}>≥ kg</label>
                        <input
                          type="number" min="0"
                          value={t.threshold}
                          onFocus={selectZeroOnFocus}
                          onChange={e => updateTier(p.local_id, idx, 'threshold', e.target.value)}
                          className={fieldCls}
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <label className={labelCls}>PLN/kg</label>
                        <input
                          type="number" step="0.1" min="0"
                          value={t.price}
                          onFocus={selectZeroOnFocus}
                          onChange={e => updateTier(p.local_id, idx, 'price', e.target.value)}
                          className={fieldCls}
                        />
                      </div>
                      <button
                        onClick={() => removeTier(p.local_id, idx)}
                        className={`${iconBtnCls} mb-0.5 border-red-200 text-red-400 hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-950 shrink-0`}
                        title="Remove tier"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </Card>
            ))}

            <button
              onClick={addWeek}
              className="flex items-center justify-center min-h-[120px] rounded-tremor-default border-2 border-dashed border-tremor-border dark:border-dark-tremor-border text-tremor-content-subtle dark:text-dark-tremor-content-subtle hover:border-tremor-brand dark:hover:border-dark-tremor-brand hover:text-tremor-brand dark:hover:text-dark-tremor-brand transition-colors text-sm"
            >
              + Add week
            </button>
          </div>
        </section>

        <section>
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-tremor-content-emphasis dark:text-dark-tremor-content-emphasis">
              Delivery parameters per building
            </p>
            <Button
              size="xs"
              variant="secondary"
              onClick={openAddDelivery}
              disabled={unusedBuildings.length === 0 || addingDelivery}
            >
              + Add building parameter
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {addingDelivery && (
              <Card className="space-y-3">
                <p className="text-sm font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong">
                  Add delivery parameter
                </p>

                <div>
                  <label className={labelCls}>Building</label>
                  <select
                    value={newDeliveryBuildingId}
                    onChange={e => setNewDeliveryBuildingId(e.target.value)}
                    className={fieldCls}
                  >
                    {unusedBuildings.map(building => (
                      <option key={building.id} value={building.id}>
                        {building.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelCls}>Lead time (days)</label>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      value={newDeliveryLeadTime}
                      onFocus={selectZeroOnFocus}
                      onChange={e => setNewDeliveryLeadTime(parseInt(e.target.value) || 0)}
                      className={fieldCls}
                    />
                  </div>
                  <div>
                    <label className={labelCls}>Fixed cost (PLN)</label>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      value={newDeliveryFixedCost}
                      onFocus={selectZeroOnFocus}
                      onChange={e => setNewDeliveryFixedCost(parseFloat(e.target.value) || 0)}
                      className={fieldCls}
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button size="xs" onClick={addDelivery} disabled={!newDeliveryBuildingId}>
                    Add parameter
                  </Button>
                  <Button size="xs" variant="secondary" onClick={cancelAddDelivery}>
                    Cancel
                  </Button>
                </div>
              </Card>
            )}

            {delivery.length === 0 && !addingDelivery && (
              <Card>
                <Text className="text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                  No delivery parameters configured yet. Add a building parameter to define delivery time and fixed cost.
                </Text>
              </Card>
            )}

            {delivery.map(dp => (
              <Card key={dp.building_id}>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <p className="text-sm font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong truncate">
                    {dp.building_name}
                  </p>
                  <button
                    onClick={() => removeDelivery(dp.building_id)}
                    className={`${iconBtnCls} border-red-200 text-red-500 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950`}
                    title="Remove delivery parameter"
                  >
                    ✕
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelCls}>Lead time (days)</label>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      value={dp.lead_time_days}
                      onFocus={selectZeroOnFocus}
                      onChange={e => updateDelivery(dp.building_id, 'lead_time_days', e.target.value)}
                      className={fieldCls}
                    />
                  </div>
                  <div>
                    <label className={labelCls}>Fixed cost (PLN)</label>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      value={dp.fixed_cost_pln}
                      onFocus={selectZeroOnFocus}
                      onChange={e => updateDelivery(dp.building_id, 'fixed_cost_pln', e.target.value)}
                      className={fieldCls}
                    />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>

        <div className="flex justify-end pb-4">
          <div className="flex items-center gap-2">
            {saving && <Text className="text-xs text-tremor-content-subtle">Saving...</Text>}
            {saved && <Text className="text-xs text-green-600">Saved ✓</Text>}
            {saveError && <Text className="text-xs text-red-500">{saveError}</Text>}
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save all changes'}
            </Button>
          </div>
        </div>
      </main>
    </div>
  )
}