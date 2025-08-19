from pipeline.main import main as run_main


from unittest.mock import MagicMock


def test_main_flow_execution_order(mock_all_tasks):
    called = []

    mock_all_tasks["get_towns"].side_effect = lambda: (called.append("get_towns"), [])[
        1
    ]
    mock_all_tasks["enrich_towns"].side_effect = lambda x: (
        called.append("enrich_towns"),
        [],
    )[1]
    mock_all_tasks["merge_data"].side_effect = lambda *a, **k: (
        called.append("merge_data"),
        [],
    )[1]
    mock_all_tasks["generate_embeddings"].side_effect = lambda x: (
        called.append("generate_embeddings"),
        ([], [], [], []),
    )[1]
    mock_all_tasks["save_data"].side_effect = lambda *a, **k: called.append("save_data")

    def _submitted(name):
        called.append(name)
        fut = MagicMock()
        fut.result.return_value = {} if name != "get_beaches" else {}
        return fut

    mock_all_tasks["get_beaches"].submit.side_effect = lambda *a, **k: _submitted(
        "get_beaches"
    )
    mock_all_tasks["get_iaph"].submit.side_effect = lambda *a, **k: _submitted(
        "get_iaph"
    )
    mock_all_tasks["upload_report"].submit.side_effect = lambda *a, **k: _submitted(
        "upload_report"
    )

    run_main()

    assert "get_towns" in called and "enrich_towns" in called and "merge_data" in called
    assert (
        called.index("get_towns")
        < called.index("enrich_towns")
        < called.index("merge_data")
    )
    assert called.index("generate_embeddings") < called.index("save_data")

    mock_all_tasks["get_beaches"].submit.assert_called_once()
    mock_all_tasks["get_iaph"].submit.assert_called_once()
    mock_all_tasks["upload_report"].submit.assert_called_once()


def test_main_flow_with_concurrent_tasks(mock_all_tasks):
    """Test que verifica el uso de ConcurrentTaskRunner"""
    # Ejecutar el flujo principal
    run_main()

    # Verificar que se llamó a submit() para las tareas concurrentes
    mock_all_tasks["get_beaches"].submit.assert_called_once()
    mock_all_tasks["get_iaph"].submit.assert_called_once()
    mock_all_tasks["upload_report"].submit.assert_called_once()

    # Verificar que se llamó a result() para obtener los resultados
    mock_all_tasks["get_beaches"].submit.return_value.result.assert_called_once()
    mock_all_tasks["get_iaph"].submit.return_value.result.assert_called_once()
    mock_all_tasks["upload_report"].submit.return_value.result.assert_called_once()


def test_main_flow_data_processing(mock_all_tasks, base_towns):
    """Test que verifica el procesamiento correcto de los datos"""
    # Configurar datos de prueba
    test_towns = [{"id": 1, "name": "Test Town"}]
    test_enriched = [{"id": 1, "name": "Test Town", "extra": "data"}]
    test_beaches = {"Test Town": True}
    test_iaph = {"Test Town": {"cultural_data": "sample"}}
    test_merged = base_towns(1, with_images=True)
    mock_all_tasks["get_towns"].return_value = test_towns
    mock_all_tasks["enrich_towns"].return_value = test_enriched
    mock_all_tasks["get_beaches"].submit.return_value.result.return_value = test_beaches
    mock_all_tasks["get_iaph"].submit.return_value.result.return_value = test_iaph
    mock_all_tasks["merge_data"].return_value = test_merged

    # Ejecutar el flujo principal
    run_main()

    # Verificar que los datos se procesaron correctamente
    mock_all_tasks["enrich_towns"].assert_called_once_with(test_towns)
    mock_all_tasks["merge_data"].assert_called_once_with(
        towns_data=test_enriched, beach_towns=test_beaches, iaph_data=test_iaph
    )
    mock_all_tasks["generate_embeddings"].assert_called_once_with(test_merged)


def test_main_flow_returns_none(mock_all_tasks):
    """Test que verifica que el flujo principal retorna None"""
    result = run_main()
    assert result is None
