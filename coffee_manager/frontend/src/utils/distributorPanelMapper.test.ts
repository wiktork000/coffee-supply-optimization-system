import { describe, expect, it } from 'vitest'
import { buildDistributorUpdatePayload } from './distributorPanelMapper'

describe('buildDistributorUpdatePayload', () => {
  it('maps panel discount tiers to API discount_tiers format', () => {
    const payload = buildDistributorUpdatePayload(
      [
        {
          local_id: 'day-1',
          day: 1,
          base_price: 28.5,
          availability_kg: 500,
          tiers: [
            { threshold: 100, price: 25 },
            { threshold: 200, price: 22.5 },
          ],
        },
      ],
      [],
    )

    expect(payload.daily_prices).toEqual([
      {
        day: 1,
        base_price: 28.5,
        availability_kg: 500,
        discount_tiers: [
          { level: 1, quantity_kg: 100, unit_price: 25 },
          { level: 2, quantity_kg: 200, unit_price: 22.5 },
        ],
      },
    ])
  })

  it('sorts daily prices by day and maps delivery params without frontend-only fields', () => {
    const payload = buildDistributorUpdatePayload(
      [
        {
          local_id: 'day-3',
          day: 3,
          base_price: 30,
          availability_kg: 200,
          tiers: [],
        },
        {
          local_id: 'day-1',
          day: 1,
          base_price: 20,
          availability_kg: 100,
          tiers: [],
        },
      ],
      [
        {
          building_id: 'b1',
          building_name: 'Budynek A',
          lead_time_days: 2,
          fixed_cost_pln: 50,
        },
      ],
    )

    expect(payload.daily_prices?.map(price => price.day)).toEqual([1, 3])
    expect(payload.delivery_params).toEqual([
      {
        building_id: 'b1',
        lead_time_days: 2,
        fixed_cost_pln: 50,
      },
    ])
  })
})