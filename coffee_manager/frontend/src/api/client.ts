import { Api } from './api'

const API_BASE_URL = 'http://localhost:8000'

const rawApi = new Api({
  baseURL: API_BASE_URL,
  securityWorker: (token: string | null) =>
    token ? { headers: { Authorization: `Bearer ${token}` } } : {},
})

const stored = localStorage.getItem('auth_token')
if (stored) rawApi.setSecurityData(stored)

rawApi.instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('auth')
      localStorage.removeItem('auth_token')
      rawApi.setSecurityData(null)
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const api = {
  setSecurityData: rawApi.setSecurityData.bind(rawApi),

  auth: {
    login: rawApi.auth.loginAuthLoginPost,
    register: rawApi.auth.registerAuthRegisterPost,
  },

  buildings: {
    listBuildings: rawApi.buildings.listBuildingsBuildingsGet,
    createBuilding: rawApi.buildings.createBuildingBuildingsPost,
    getBuilding: rawApi.buildings.getBuildingBuildingsBuildingIdGet,
    updateBuilding: rawApi.buildings.updateBuildingBuildingsBuildingIdPut,
    deleteBuilding: rawApi.buildings.deleteBuildingBuildingsBuildingIdDelete,
  },

  distributors: {
    listDistributors: rawApi.distributors.listDistributorsDistributorsGet,
    createDistributor: rawApi.distributors.createDistributorDistributorsPost,
    getDistributor: rawApi.distributors.getDistributorDistributorsDistributorIdGet,
    updateDistributor: rawApi.distributors.updateDistributorDistributorsDistributorIdPut,
    deleteDistributor: rawApi.distributors.deleteDistributorDistributorsDistributorIdDelete,
    getOwnPrices: rawApi.distributors.getOwnPricesDistributorsSelfPricesGet,
    updateOwnPrices: rawApi.distributors.updateOwnPricesDistributorsSelfPricesPut,
    getOwnAvailableBuildings: rawApi.distributors.getOwnAvailableBuildingsDistributorsSelfAvailableBuildingsGet,
    listApiKeys: rawApi.distributors.listApiKeysDistributorsDistributorIdApiKeysGet,
    createApiKey: rawApi.distributors.createApiKeyDistributorsDistributorIdApiKeysPost,
  },

  inventory: {
    getInventory: rawApi.inventory.getInventoryInventoryGet,
    updateInventory: rawApi.inventory.updateInventoryInventoryBuildingIdPut,
  },

  optimization: {
    listOptimizations: rawApi.optimization.listOptimizationsOptimizationGet,
    runOptimization: rawApi.optimization.runOptimizationOptimizationPost,
    getOptimizationResult: rawApi.optimization.getOptimizationResultOptimizationResultIdGet,
    runCorrection: rawApi.optimization.runCorrectionOptimizationCorrectionPost,
  },

  orders: {
    listOrders: rawApi.orders.listOrdersOrdersGet,
    confirmOrders: rawApi.orders.confirmOrdersOrdersPost,
    getOrder: rawApi.orders.getOrderOrdersOrderIdGet,
    updateOrderStatus: rawApi.orders.updateOrderStatusOrdersOrderIdStatusPatch,
  },
}