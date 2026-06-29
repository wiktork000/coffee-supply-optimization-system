import type { DistributorUpdateRequest } from '../api/api'

export type PanelTier = {
  threshold: number
  price: number
}

export type PanelDayPrice = {
  local_id: string
  day: number
  base_price: number
  availability_kg: number
  tiers: PanelTier[]
}

export type PanelDeliveryParam = {
  building_id: string
  building_name: string
  lead_time_days: number
  fixed_cost_pln: number
}

export const buildDistributorUpdatePayload = (
  prices: PanelDayPrice[],
  delivery: PanelDeliveryParam[],
): DistributorUpdateRequest => ({
  daily_prices: [...prices]
    .sort((a, b) => a.day - b.day)
    .map(price => ({
      day: price.day,
      base_price: price.base_price,
      availability_kg: price.availability_kg,
      discount_tiers: price.tiers.map((tier, index) => ({
        level: index + 1,
        quantity_kg: tier.threshold,
        unit_price: tier.price,
      })),
    })),
  delivery_params: delivery.map(param => ({
    building_id: param.building_id,
    lead_time_days: param.lead_time_days,
    fixed_cost_pln: param.fixed_cost_pln,
  })),
})