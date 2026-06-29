  # Coffee Ordering System — Docs

| Doc | Contents |
|---|---|
| [architecture.md](architecture.md) | Architecture overview — logical + hardware views, backed by UML diagrams |
| [infrastructure.md](infrastructure.md) | Components, ports, containers, networking, persistence, config |
| [api.md](api.md) | Endpoint reference for `coffee_manager` and `coffee_optimizer` (see `swagger.yaml` for the full spec) |
| [workflows.md](workflows.md) | End-to-end flows: auth, catalog setup, optimization, order lifecycle |
| [diagrams/component-diagram.drawio](diagrams/component-diagram.drawio) | UML — component diagram (logical view, interfaces) |
| [diagrams/deployment-diagram.drawio](diagrams/deployment-diagram.drawio) | UML — deployment diagram (hardware view, containers) |
| [diagrams/class-diagram.drawio](diagrams/class-diagram.drawio) | UML — class diagram (domain model) |
| [diagrams/architecture.drawio](diagrams/architecture.drawio) | Simplified combined view of components and deployment |
| [diagrams/optimization-workflow.drawio](diagrams/optimization-workflow.drawio) | Sequence diagram for `POST /optimization` |
| [diagrams/order-workflow.drawio](diagrams/order-workflow.drawio) | Order state machine + inventory feedback loop |

