{% for dataset in datasets %}
SELECT '{{ dataset }}' AS dataset, table_id AS tabela, row_count AS linhas, size_bytes AS bytes
FROM `{{ project }}.{{ dataset }}.__TABLES__`
{{ "UNION ALL" if not loop.last else "" }}
{% endfor %}
ORDER BY dataset, tabela;
