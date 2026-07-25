import { createRootRoute, createRoute } from '@tanstack/react-router'
import { UploadScreen } from './routes/upload'
import { ResultsScreen } from './routes/results'

const rootRoute = createRootRoute()

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: UploadScreen,
})

const resultsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/results',
  component: ResultsScreen,
})

export const routeTree = rootRoute.addChildren([indexRoute, resultsRoute])
