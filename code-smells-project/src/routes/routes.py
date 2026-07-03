from src.controllers import pedido_controller, produto_controller, sistema_controller, usuario_controller
from src.middlewares.auth import require_admin, require_auth, require_owner_or_admin


def register_routes(app):
    app.add_url_rule("/", "index", sistema_controller.index, methods=["GET"])
    app.add_url_rule("/health", "health_check", sistema_controller.health_check, methods=["GET"])

    app.add_url_rule(
        "/produtos", "listar_produtos", produto_controller.listar_produtos, methods=["GET"]
    )
    app.add_url_rule(
        "/produtos/busca", "buscar_produtos", produto_controller.buscar_produtos, methods=["GET"]
    )
    app.add_url_rule(
        "/produtos/<int:id>", "buscar_produto", produto_controller.buscar_produto, methods=["GET"]
    )
    app.add_url_rule(
        "/produtos",
        "criar_produto",
        require_admin(produto_controller.criar_produto),
        methods=["POST"],
    )
    app.add_url_rule(
        "/produtos/<int:id>",
        "atualizar_produto",
        require_admin(produto_controller.atualizar_produto),
        methods=["PUT"],
    )
    app.add_url_rule(
        "/produtos/<int:id>",
        "deletar_produto",
        require_admin(produto_controller.deletar_produto),
        methods=["DELETE"],
    )

    app.add_url_rule(
        "/usuarios",
        "listar_usuarios",
        require_admin(usuario_controller.listar_usuarios),
        methods=["GET"],
    )
    app.add_url_rule(
        "/usuarios/<int:id>",
        "buscar_usuario",
        require_owner_or_admin("id")(usuario_controller.buscar_usuario),
        methods=["GET"],
    )
    app.add_url_rule(
        "/usuarios", "criar_usuario", usuario_controller.criar_usuario, methods=["POST"]
    )
    app.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])

    app.add_url_rule(
        "/pedidos", "criar_pedido", require_auth(pedido_controller.criar_pedido), methods=["POST"]
    )
    app.add_url_rule(
        "/pedidos",
        "listar_todos_pedidos",
        require_admin(pedido_controller.listar_todos_pedidos),
        methods=["GET"],
    )
    app.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>",
        "listar_pedidos_usuario",
        require_owner_or_admin("usuario_id")(pedido_controller.listar_pedidos_usuario),
        methods=["GET"],
    )
    app.add_url_rule(
        "/pedidos/<int:pedido_id>/status",
        "atualizar_status_pedido",
        require_admin(pedido_controller.atualizar_status_pedido),
        methods=["PUT"],
    )

    app.add_url_rule(
        "/relatorios/vendas",
        "relatorio_vendas",
        sistema_controller.relatorio_vendas,
        methods=["GET"],
    )

    app.add_url_rule(
        "/admin/reset-db",
        "reset_database",
        require_admin(sistema_controller.reset_database),
        methods=["POST"],
    )
