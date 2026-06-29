/* eslint-disable */
/* tslint:disable */
// @ts-nocheck


/** ApiKeyCreateRequest */
export interface ApiKeyCreateRequest {
  /** Label */
  label: string;
}

/** ApiKeyResponse */
export interface ApiKeyResponse {
  /**
   * Id
   * @format uuid
   */
  id: string;
  /** Key */
  key?: string | null;
  /** Label */
  label: string;
  /**
   * Distributor Id
   * @format uuid
   */
  distributor_id: string;
  /** Active */
  active: boolean;
  /** Revoked At */
  revoked_at: string | null;
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
}

/** BuildingCreateRequest */
export interface BuildingCreateRequest {
  /** Name */
  name: string;
  /** Location */
  location?: string | null;
  /**
   * Max Capacity Kg
   * @min 0
   */
  max_capacity_kg: number;
  /**
   * Initial Inventory Kg
   * @min 0
   * @default 0
   */
  initial_inventory_kg?: number;
  /** Daily Demand */
  daily_demand: DailyDemand[];
}

/** BuildingResponse */
export interface BuildingResponse {
  /**
   * Id
   * @format uuid
   */
  id: string;
  /** Name */
  name: string;
  /** Location */
  location: string | null;
  /** Max Capacity Kg */
  max_capacity_kg: number;
  /** Initial Inventory Kg */
  initial_inventory_kg: number;
  /** Current Inventory Kg */
  current_inventory_kg: number;
  /** Daily Demand */
  daily_demand: DailyDemand[];
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
  /**
   * Updated At
   * @format date-time
   */
  updated_at: string;
}

/** CostBreakdown */
export interface CostBreakdown {
  /** Purchase Base */
  purchase_base: number;
  /** Purchase Discount */
  purchase_discount: number;
  /** Fixed Delivery */
  fixed_delivery: number;
  /** Total */
  total: number;
}

/** DailyDemand */
export interface DailyDemand {
  /**
   * Day
   * @min 1
   */
  day: number;
  /**
   * Demand Kg
   * @min 0
   */
  demand_kg: number;
}

/** DailyPrice */
export interface DailyPrice {
  /**
   * Day
   * @min 1
   */
  day: number;
  /**
   * Base Price
   * @min 0
   */
  base_price: number;
  /**
   * Availability Kg
   * @min 0
   */
  availability_kg: number;
  /**
   * Discount Tiers
   * @default []
   */
  discount_tiers?: DiscountTier[];
}

/** DeliveryParams */
export interface DeliveryParams {
  /** Building Id */
  building_id: string;
  /**
   * Lead Time Days
   * @min 0
   */
  lead_time_days: number;
  /**
   * Fixed Cost Pln
   * @min 0
   */
  fixed_cost_pln: number;
  /**
   * Correction Cost Per Kg
   * @min 0
   * @default 0
   */
  correction_cost_per_kg?: number;
  /**
   * Max Correction Kg
   * @min 0
   * @default 1000000
   */
  max_correction_kg?: number;
}

/** DiscountTier */
export interface DiscountTier {
  /**
   * Level
   * @min 1
   */
  level: number;
  /**
   * Quantity Kg
   * @min 0
   */
  quantity_kg: number;
  /**
   * Unit Price
   * @min 0
   */
  unit_price: number;
}

/** DistributorCreateRequest */
export interface DistributorCreateRequest {
  /** Username */
  username: string;
  /** Contact Email */
  contact_email: string;
  /** Contact Phone */
  contact_phone: string;
  /** Daily Prices */
  daily_prices: DailyPrice[];
  /** Delivery Params */
  delivery_params: DeliveryParams[];
}

/** DistributorResponse */
export interface DistributorResponse {
  /**
   * Id
   * @format uuid
   */
  id: string;
  /** Username */
  username: string;
  /** Contact Email */
  contact_email: string;
  /** Contact Phone */
  contact_phone: string;
  /** Active */
  active: boolean;
  /** Daily Prices */
  daily_prices: DailyPrice[];
  /** Delivery Params */
  delivery_params: DeliveryParams[];
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
  /**
   * Updated At
   * @format date-time
   */
  updated_at: string;
}

/** DistributorUpdateRequest */
export interface DistributorUpdateRequest {
  /** Username */
  username?: string | null;
  /** Contact Email */
  contact_email?: string | null;
  /** Contact Phone */
  contact_phone?: string | null;
  /** Daily Prices */
  daily_prices?: DailyPrice[] | null;
  /** Delivery Params */
  delivery_params?: DeliveryParams[] | null;
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/** InventoryLevel */
export interface InventoryLevel {
  /**
   * Building Id
   * @format uuid
   */
  building_id: string;
  /** Day */
  day: number;
  /** Level Kg */
  level_kg: number;
}

/** InventoryStatus */
export interface InventoryStatus {
  /**
   * Building Id
   * @format uuid
   */
  building_id: string;
  /** Building Name */
  building_name: string;
  /** Current Inventory Kg */
  current_inventory_kg: number;
  /** Max Capacity Kg */
  max_capacity_kg: number;
  /** Fill Percent */
  fill_percent: number;
}

/** LoginRequest */
export interface LoginRequest {
  /** Username */
  username: string;
  /** Password */
  password: string;
}

/** LoginResponse */
export interface LoginResponse {
  /** Token */
  token: string;
  /**
   * User Id
   * @format uuid
   */
  user_id: string;
  /** Role */
  role: string;
}

/** OptimizationResponse */
export interface OptimizationResponse {
  /**
   * Scenario Id
   * @format uuid
   */
  scenario_id: string;
  /**
   * Result Id
   * @format uuid
   */
  result_id: string;
  /** Status */
  status: string;
  /** Total Cost Pln */
  total_cost_pln: number | null;
  /** Solver Message */
  solver_message: string | null;
  /** Orders */
  orders: OrderItem[];
  /** Inventory Levels */
  inventory_levels: InventoryLevel[];
  cost_breakdown: CostBreakdown | null;
}

/** CorrectionRequest */
export interface CorrectionRequest {
  /** Name */
  name: string;
  /**
   * Previous Result Id
   * @format uuid
   */
  previous_result_id: string;
  /** Historical Orders */
  historical_orders?: Record<string, any> | null;
}

/** CorrectionItem */
export interface CorrectionItem {
  /**
   * Distributor Id
   * @format uuid
   */
  distributor_id: string;
  /**
   * Building Id
   * @format uuid
   */
  building_id: string;
  /** Day */
  day: number;
  /** Threshold Level */
  threshold_level: number;
  /** Type */
  type: string;
  /** Quantity Kg */
  quantity_kg: number;
}

/** CorrectionResponse */
export interface CorrectionResponse {
  /**
   * Scenario Id
   * @format uuid
   */
  scenario_id: string;
  /**
   * Result Id
   * @format uuid
   */
  result_id: string;
  /** Status */
  status: string;
  /** Total Cost Pln */
  total_cost_pln: number | null;
  /** Solver Message */
  solver_message: string | null;
  /** Orders */
  orders: OrderItem[];
  /** Corrections */
  corrections: CorrectionItem[];
  /** Inventory Levels */
  inventory_levels: InventoryLevel[];
}

/** OrderItem */
export interface OrderItem {
  /**
   * Distributor Id
   * @format uuid
   */
  distributor_id: string;
  /**
   * Building Id
   * @format uuid
   */
  building_id: string;
  /**
   * Day
   * @min 1
   */
  day: number;
  /**
   * Threshold Level
   * @min 0
   */
  threshold_level: number;
  /**
   * Quantity Kg
   * @min 0
   */
  quantity_kg: number;
}

/** OrderRecord */
export interface OrderRecord {
  /**
   * Id
   * @format uuid
   */
  id: string;
  /**
   * Result Id
   * @format uuid
   */
  result_id: string;
  /**
   * Scenario Id
   * @format uuid
   */
  scenario_id: string;
  /** Orders */
  orders: OrderItem[];
  /** Total Cost Pln */
  total_cost_pln: number | null;
  /** Confirmed By */
  confirmed_by: string | null;
  /** Status */
  status: string;
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
  /**
   * Updated At
   * @format date-time
   */
  updated_at: string;
}

/** OrderStatusUpdate */
export interface OrderStatusUpdate {
  /**
   * Status
   * @pattern ^(confirmed|pending|cancelled)$
   */
  status: string;
}

/** ScenarioCreateRequest */
export interface ScenarioCreateRequest {
  /** Name */
  name: string;
  /**
   * Planning Horizon Days
   * @min 1
   * @max 30
   * @default 7
   */
  planning_horizon_days?: number;
  /** Distributor Ids */
  distributor_ids: string[];
  /** Building Ids */
  building_ids: string[];
  /**
   * Decay Rate
   * @min 0
   * @max 1
   * @default 0.05
   */
  decay_rate?: number;
  /** Historical Orders */
  historical_orders?: Record<string, any> | null;
}

/** ValidationError */
export interface ValidationError {
  /** Location */
  loc: (string | number)[];
  /** Message */
  msg: string;
  /** Error Type */
  type: string;
  /** Input */
  input?: any;
  /** Context */
  ctx?: object;
}

import type {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  HeadersDefaults,
  ResponseType,
} from "axios";
import axios from "axios";

export type QueryParamsType = Record<string | number, any>;

export interface FullRequestParams
  extends Omit<AxiosRequestConfig, "data" | "params" | "url" | "responseType"> {
  /** set parameter to `true` for call `securityWorker` for this request */
  secure?: boolean;
  /** request path */
  path: string;
  /** content type of request body */
  type?: ContentType;
  /** query params */
  query?: QueryParamsType;
  /** format of response (i.e. response.json() -> format: "json") */
  format?: ResponseType;
  /** request body */
  body?: unknown;
}

export type RequestParams = Omit<
  FullRequestParams,
  "body" | "method" | "query" | "path"
>;

export interface ApiConfig<SecurityDataType = unknown>
  extends Omit<AxiosRequestConfig, "data" | "cancelToken"> {
  securityWorker?: (
    securityData: SecurityDataType | null,
  ) => Promise<AxiosRequestConfig | void> | AxiosRequestConfig | void;
  secure?: boolean;
  format?: ResponseType;
}

export enum ContentType {
  Json = "application/json",
  JsonApi = "application/vnd.api+json",
  FormData = "multipart/form-data",
  UrlEncoded = "application/x-www-form-urlencoded",
  Text = "text/plain",
}

export class HttpClient<SecurityDataType = unknown> {
  public instance: AxiosInstance;
  private securityData: SecurityDataType | null = null;
  private securityWorker?: ApiConfig<SecurityDataType>["securityWorker"];
  private secure?: boolean;
  private format?: ResponseType;

  constructor({
    securityWorker,
    secure,
    format,
    ...axiosConfig
  }: ApiConfig<SecurityDataType> = {}) {
    this.instance = axios.create({
      ...axiosConfig,
      baseURL: axiosConfig.baseURL || "",
    });
    this.secure = secure;
    this.format = format;
    this.securityWorker = securityWorker;
  }

  public setSecurityData = (data: SecurityDataType | null) => {
    this.securityData = data;
  };

  protected mergeRequestParams(
    params1: AxiosRequestConfig,
    params2?: AxiosRequestConfig,
  ): AxiosRequestConfig {
    const method = params1.method || (params2 && params2.method);

    return {
      ...this.instance.defaults,
      ...params1,
      ...(params2 || {}),
      headers: {
        ...((method &&
          this.instance.defaults.headers[
            method.toLowerCase() as keyof HeadersDefaults
          ]) ||
          {}),
        ...(params1.headers || {}),
        ...((params2 && params2.headers) || {}),
      },
    };
  }

  protected stringifyFormItem(formItem: unknown) {
    if (typeof formItem === "object" && formItem !== null) {
      return JSON.stringify(formItem);
    } else {
      return `${formItem}`;
    }
  }

  protected createFormData(input: Record<string, unknown>): FormData {
    if (input instanceof FormData) {
      return input;
    }
    return Object.keys(input || {}).reduce((formData, key) => {
      const property = input[key];
      const propertyContent: any[] =
        property instanceof Array ? property : [property];

      for (const formItem of propertyContent) {
        const isFileType = formItem instanceof Blob || formItem instanceof File;
        formData.append(
          key,
          isFileType ? formItem : this.stringifyFormItem(formItem),
        );
      }

      return formData;
    }, new FormData());
  }

  public request = async <T = any, _E = any>({
    secure,
    path,
    type,
    query,
    format,
    body,
    ...params
  }: FullRequestParams): Promise<AxiosResponse<T>> => {
    const secureParams =
      ((typeof secure === "boolean" ? secure : this.secure) &&
        this.securityWorker &&
        (await this.securityWorker(this.securityData))) ||
      {};
    const requestParams = this.mergeRequestParams(params, secureParams);
    const responseFormat = format || this.format || undefined;

    if (
      type === ContentType.FormData &&
      body &&
      body !== null &&
      typeof body === "object"
    ) {
      body = this.createFormData(body as Record<string, unknown>);
    }

    if (
      type === ContentType.Text &&
      body &&
      body !== null &&
      typeof body !== "string"
    ) {
      body = JSON.stringify(body);
    }

    return this.instance.request({
      ...requestParams,
      headers: {
        ...(requestParams.headers || {}),
        ...(type ? { "Content-Type": type } : {}),
      },
      params: query,
      responseType: responseFormat,
      data: body,
      url: path,
    });
  };
}

/**
 * @title Coffee Supply Management API
 * @version 1.0.0
 */
export class Api<
  SecurityDataType extends unknown,
> extends HttpClient<SecurityDataType> {
  auth = {
    /**
     * No description
     *
     * @tags Authentication
     * @name LoginAuthLoginPost
     * @summary Login
     * @request POST:/auth/login
     */
    loginAuthLoginPost: (data: LoginRequest, params: RequestParams = {}) =>
      this.request<LoginResponse, HTTPValidationError>({
        path: `/auth/login`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Authentication
     * @name RegisterAuthRegisterPost
     * @summary Register
     * @request POST:/auth/register
     */
    registerAuthRegisterPost: (
      data: LoginRequest,
      params: RequestParams = {},
    ) =>
      this.request<LoginResponse, HTTPValidationError>({
        path: `/auth/register`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  distributors = {
    /**
     * No description
     *
     * @tags Distributors
     * @name ListDistributorsDistributorsGet
     * @summary List Distributors
     * @request GET:/distributors
     * @secure
     */
    listDistributorsDistributorsGet: (params: RequestParams = {}) =>
      this.request<DistributorResponse[], any>({
        path: `/distributors`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Distributors
     * @name CreateDistributorDistributorsPost
     * @summary Create Distributor
     * @request POST:/distributors
     * @secure
     */
    createDistributorDistributorsPost: (
      data: DistributorCreateRequest,
      params: RequestParams = {},
    ) =>
      this.request<DistributorResponse, HTTPValidationError>({
        path: `/distributors`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Distributors, Distributors - Self Service
     * @name GetOwnPricesDistributorsSelfPricesGet
     * @summary Get Own Prices
     * @request GET:/distributors/self/prices
     * @secure
     */
    getOwnPricesDistributorsSelfPricesGet: (params: RequestParams = {}) =>
      this.request<DistributorResponse, any>({
        path: `/distributors/self/prices`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Distributors, Distributors - Self Service
     * @name UpdateOwnPricesDistributorsSelfPricesPut
     * @summary Update Own Prices
     * @request PUT:/distributors/self/prices
     * @secure
     */
    updateOwnPricesDistributorsSelfPricesPut: (
      data: DistributorUpdateRequest,
      params: RequestParams = {},
    ) =>
      this.request<DistributorResponse, HTTPValidationError>({
        path: `/distributors/self/prices`,
        method: "PUT",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Distributors, Distributors - Self Service
     * @name GetOwnAvailableBuildingsDistributorsSelfAvailableBuildingsGet
     * @summary Get Own Available Buildings
     * @request GET:/distributors/self/available-buildings
     * @secure
     */
    getOwnAvailableBuildingsDistributorsSelfAvailableBuildingsGet: (
      params: RequestParams = {},
    ) =>
      this.request<BuildingResponse[], any>({
        path: `/distributors/self/available-buildings`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Distributors
     * @name GetDistributorDistributorsDistributorIdGet
     * @summary Get Distributor
     * @request GET:/distributors/{distributor_id}
     * @secure
     */
    getDistributorDistributorsDistributorIdGet: (
      distributorId: string,
      params: RequestParams = {},
    ) =>
      this.request<DistributorResponse, HTTPValidationError>({
        path: `/distributors/${distributorId}`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Distributors
     * @name UpdateDistributorDistributorsDistributorIdPut
     * @summary Update Distributor
     * @request PUT:/distributors/{distributor_id}
     * @secure
     */
    updateDistributorDistributorsDistributorIdPut: (
      distributorId: string,
      data: DistributorUpdateRequest,
      params: RequestParams = {},
    ) =>
      this.request<DistributorResponse, HTTPValidationError>({
        path: `/distributors/${distributorId}`,
        method: "PUT",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Distributors
     * @name DeleteDistributorDistributorsDistributorIdDelete
     * @summary Delete Distributor
     * @request DELETE:/distributors/{distributor_id}
     * @secure
     */
    deleteDistributorDistributorsDistributorIdDelete: (
      distributorId: string,
      params: RequestParams = {},
    ) =>
      this.request<void, HTTPValidationError>({
        path: `/distributors/${distributorId}`,
        method: "DELETE",
        secure: true,
        ...params,
      }),

    /**
     * No description
     *
     * @tags API Keys
     * @name ListApiKeysDistributorsDistributorIdApiKeysGet
     * @summary List Api Keys
     * @request GET:/distributors/{distributor_id}/api-keys
     * @secure
     */
    listApiKeysDistributorsDistributorIdApiKeysGet: (
      distributorId: string,
      params: RequestParams = {},
    ) =>
      this.request<ApiKeyResponse[], HTTPValidationError>({
        path: `/distributors/${distributorId}/api-keys`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags API Keys
     * @name CreateApiKeyDistributorsDistributorIdApiKeysPost
     * @summary Create Api Key
     * @request POST:/distributors/{distributor_id}/api-keys
     * @secure
     */
    createApiKeyDistributorsDistributorIdApiKeysPost: (
      distributorId: string,
      data: ApiKeyCreateRequest,
      params: RequestParams = {},
    ) =>
      this.request<ApiKeyResponse, HTTPValidationError>({
        path: `/distributors/${distributorId}/api-keys`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  apiKeys = {
    /**
     * No description
     *
     * @tags API Keys
     * @name RevokeApiKeyApiKeysKeyIdDelete
     * @summary Revoke Api Key
     * @request DELETE:/api-keys/{key_id}
     * @secure
     */
    revokeApiKeyApiKeysKeyIdDelete: (
      keyId: string,
      params: RequestParams = {},
    ) =>
      this.request<void, HTTPValidationError>({
        path: `/api-keys/${keyId}`,
        method: "DELETE",
        secure: true,
        ...params,
      }),
  };
  buildings = {
    /**
     * No description
     *
     * @tags Buildings
     * @name ListBuildingsBuildingsGet
     * @summary List Buildings
     * @request GET:/buildings
     * @secure
     */
    listBuildingsBuildingsGet: (params: RequestParams = {}) =>
      this.request<BuildingResponse[], any>({
        path: `/buildings`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Buildings
     * @name CreateBuildingBuildingsPost
     * @summary Create Building
     * @request POST:/buildings
     * @secure
     */
    createBuildingBuildingsPost: (
      data: BuildingCreateRequest,
      params: RequestParams = {},
    ) =>
      this.request<BuildingResponse, HTTPValidationError>({
        path: `/buildings`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Buildings
     * @name GetBuildingBuildingsBuildingIdGet
     * @summary Get Building
     * @request GET:/buildings/{building_id}
     * @secure
     */
    getBuildingBuildingsBuildingIdGet: (
      buildingId: string,
      params: RequestParams = {},
    ) =>
      this.request<BuildingResponse, HTTPValidationError>({
        path: `/buildings/${buildingId}`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Buildings
     * @name UpdateBuildingBuildingsBuildingIdPut
     * @summary Update Building
     * @request PUT:/buildings/{building_id}
     * @secure
     */
    updateBuildingBuildingsBuildingIdPut: (
      buildingId: string,
      data: BuildingCreateRequest,
      params: RequestParams = {},
    ) =>
      this.request<BuildingResponse, HTTPValidationError>({
        path: `/buildings/${buildingId}`,
        method: "PUT",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Buildings
     * @name DeleteBuildingBuildingsBuildingIdDelete
     * @summary Delete Building
     * @request DELETE:/buildings/{building_id}
     * @secure
     */
    deleteBuildingBuildingsBuildingIdDelete: (
      buildingId: string,
      params: RequestParams = {},
    ) =>
      this.request<void, HTTPValidationError>({
        path: `/buildings/${buildingId}`,
        method: "DELETE",
        secure: true,
        ...params,
      }),
  };
  inventory = {
    /**
     * No description
     *
     * @tags Inventory
     * @name GetInventoryInventoryGet
     * @summary Get Inventory
     * @request GET:/inventory
     * @secure
     */
    getInventoryInventoryGet: (params: RequestParams = {}) =>
      this.request<InventoryStatus[], any>({
        path: `/inventory`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Inventory
     * @name UpdateInventoryInventoryBuildingIdPut
     * @summary Update Inventory
     * @request PUT:/inventory/{building_id}
     * @secure
     */
    updateInventoryInventoryBuildingIdPut: (
      buildingId: string,
      query: {
        /** Current Kg */
        current_kg: number;
      },
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/inventory/${buildingId}`,
        method: "PUT",
        query: query,
        secure: true,
        format: "json",
        ...params,
      }),
  };
  orders = {
    /**
     * No description
     *
     * @tags Orders
     * @name ListOrdersOrdersGet
     * @summary List Orders
     * @request GET:/orders
     * @secure
     */
    listOrdersOrdersGet: (
      query?: {
        /** Status */
        status?: string | null;
      },
      params: RequestParams = {},
    ) =>
      this.request<OrderRecord[], HTTPValidationError>({
        path: `/orders`,
        method: "GET",
        query: query,
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Orders
     * @name ConfirmOrdersOrdersPost
     * @summary Confirm Orders
     * @request POST:/orders
     * @secure
     */
    confirmOrdersOrdersPost: (
      query: {
        /** Result Id */
        result_id: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<OrderRecord, HTTPValidationError>({
        path: `/orders`,
        method: "POST",
        query: query,
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Orders
     * @name GetOrderOrdersOrderIdGet
     * @summary Get Order
     * @request GET:/orders/{order_id}
     * @secure
     */
    getOrderOrdersOrderIdGet: (orderId: string, params: RequestParams = {}) =>
      this.request<OrderRecord, HTTPValidationError>({
        path: `/orders/${orderId}`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Orders
     * @name UpdateOrderStatusOrdersOrderIdStatusPatch
     * @summary Update Order Status
     * @request PATCH:/orders/{order_id}/status
     * @secure
     */
    updateOrderStatusOrdersOrderIdStatusPatch: (
      orderId: string,
      data: OrderStatusUpdate,
      params: RequestParams = {},
    ) =>
      this.request<OrderRecord, HTTPValidationError>({
        path: `/orders/${orderId}/status`,
        method: "PATCH",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  optimization = {
    /**
     * No description
     *
     * @tags Optimization
     * @name ListOptimizationsOptimizationGet
     * @summary List Optimizations
     * @request GET:/optimization
     * @secure
     */
    listOptimizationsOptimizationGet: (params: RequestParams = {}) =>
      this.request<OptimizationResponse[], any>({
        path: `/optimization`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Optimization
     * @name RunOptimizationOptimizationPost
     * @summary Run Optimization
     * @request POST:/optimization
     * @secure
     */
    runOptimizationOptimizationPost: (
      data: ScenarioCreateRequest,
      params: RequestParams = {},
    ) =>
      this.request<OptimizationResponse, HTTPValidationError>({
        path: `/optimization`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags Optimization
     * @name GetOptimizationResultOptimizationResultIdGet
     * @summary Get Optimization Result
     * @request GET:/optimization/{result_id}
     * @secure
     */
    getOptimizationResultOptimizationResultIdGet: (
      resultId: string,
      params: RequestParams = {},
    ) =>
      this.request<OptimizationResponse, HTTPValidationError>({
        path: `/optimization/${resultId}`,
        method: "GET",
        secure: true,
        format: "json",
        ...params,
      }),

    /**
     * @tags Optimization
     * @name RunCorrectionOptimizationCorrectionPost
     * @summary Run Correction
     * @request POST:/optimization/correction
     * @secure
     */
    runCorrectionOptimizationCorrectionPost: (
      data: CorrectionRequest,
      params: RequestParams = {},
    ) =>
      this.request<CorrectionResponse, HTTPValidationError>({
        path: `/optimization/correction`,
        method: "POST",
        body: data,
        secure: true,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  health = {
    /**
     * No description
     *
     * @tags System
     * @name HealthCheckHealthGet
     * @summary Health Check
     * @request GET:/health
     */
    healthCheckHealthGet: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/health`,
        method: "GET",
        format: "json",
        ...params,
      }),
  };
}
