import { useEffect, useMemo, useState } from 'react';
import { Button, Stack, TextInput, Title, Text, Divider, Paper, Group, Code, List, Badge } from '@mantine/core';
import { fetchParameters, updateParameters, fetchConfig } from '../services/api';
import type { ScoringParameter, ConfigSummary } from '../services/api';

export function AdminPage() {
    const [params, setParams] = useState<ScoringParameter[]>([]);
    const [config, setConfig] = useState<ConfigSummary | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [draft, setDraft] = useState<Record<string, string>>({});

    useEffect(() => {
        fetchParameters().then(setParams);
        fetchConfig().then(setConfig);
    }, []);

    const [draftInitialized, setDraftInitialized] = useState(false);
    useEffect(() => {
        if (!draftInitialized && params.length > 0) {
            const next: Record<string, string> = {};
            params.forEach((p) => {
                next[p.param_name] = String(p.param_value ?? '');
            });
            setDraft(next);
            setDraftInitialized(true);
        }
    }, [params, draftInitialized]);

    const commitNumeric = (p: ScoringParameter, value: string) => {
        const num = parseFloat(value);
        if (!isNaN(num)) {
            setParams((prev) => prev.map((x) => (x.id === p.id ? { ...x, param_value: num } : x)));
        }
    };

    const handleInputChange = (p: ScoringParameter, value: string) => {
        // Разрешаем промежуточные значения: "", "-", "0.", и т.п.
        setDraft((prev) => ({ ...prev, [p.param_name]: value }));
        // Если строка выглядит как число — коммитим
        if (/^[-+]?\d*(?:[\.,]\d+)?$/.test(value)) {
            const normalized = value.replace(',', '.');
            commitNumeric(p, normalized);
        }
    };

    const handleInputBlur = (p: ScoringParameter) => {
        const v = (draft[p.param_name] ?? '').replace(',', '.');
        const num = parseFloat(v);
        if (isNaN(num)) {
            // Возвращаемся к текущему числовому значению параметра
            setDraft((prev) => ({ ...prev, [p.param_name]: String(params.find((x) => x.id === p.id)?.param_value ?? '') }));
        } else {
            // Нормализуем драфт к числу
            setDraft((prev) => ({ ...prev, [p.param_name]: String(num) }));
            commitNumeric(p, String(num));
        }
    };

    const handleSubmit = async () => {
        setIsLoading(true);
        await updateParameters(params);
        setIsLoading(false);
        // Optionally, show a notification
    };

    const getParamDescription = (paramName: string) => {
        switch (paramName) {
            case "W_tx": return "Вес ускорения транзакций (Tx_Accel)";
            case "W_vol": return "Вес импульса объема (Vol_Momentum)";
            case "W_hld": return "Вес роста холдеров (Holder_Growth)";
            case "W_oi": return "Вес дисбаланса потока ордеров (Orderflow_Imbalance)";
            case "EWMA_ALPHA": return "Коэффициент сглаживания EWMA (Экспоненциальное скользящее среднее)";
            case "POLLING_INTERVAL_INITIAL": return "Интервал опроса токенов в статусе 'Начальные'";
            case "POLLING_INTERVAL_ACTIVE": return "Интервал опроса токенов в статусе 'Активные'";
            case "POLLING_INTERVAL_ARCHIVED": return "Интервал опроса токенов в статусе 'Архивные'";
            case "MIN_SCORE_THRESHOLD": return "Минимальный порог скора для статуса 'Активные'";
            case "MIN_SCORE_DURATION_HOURS": return "Длительность низкого скора для смены статуса (часы)";
            case "MIN_LIQUIDITY_USD": return "Минимальная ликвидность (USD) для активации";
            case "MIN_TX_COUNT": return "Минимальное количество транзакций (за 1 час) для активации";
            default: return "";
        }
    };

    const generalParams = useMemo(() => (
        ["EWMA_ALPHA", "MIN_SCORE_THRESHOLD", "MIN_SCORE_DURATION_HOURS", "W_tx", "W_vol", "W_hld", "W_oi"]
            .map(name => params.find(p => p.param_name === name)).filter(Boolean) as ScoringParameter[]
    ), [params]);

    const initialParams = useMemo(() => (
        ["POLLING_INTERVAL_INITIAL", "MIN_LIQUIDITY_USD", "MIN_TX_COUNT"]
            .map(name => params.find(p => p.param_name === name)).filter(Boolean) as ScoringParameter[]
    ), [params]);

    const activeParams = useMemo(() => (
        ["POLLING_INTERVAL_ACTIVE"].map(name => params.find(p => p.param_name === name)).filter(Boolean) as ScoringParameter[]
    ), [params]);

    const archivedParams = useMemo(() => (
        ["POLLING_INTERVAL_ARCHIVED"].map(name => params.find(p => p.param_name === name)).filter(Boolean) as ScoringParameter[]
    ), [params]);

    const ParamField = ({ p }: { p: ScoringParameter }) => (
        <TextInput
            label={getParamDescription(p.param_name) + (p.param_name.startsWith("POLLING_INTERVAL") ? " (секунды)" : "")}
            description={p.param_name.startsWith("POLLING_INTERVAL") && p.param_value === 0 ? "(0 означает отключено)" : p.param_name}
            value={draft[p.param_name] ?? ''}
            onChange={(event) => handleInputChange(p, event.currentTarget.value)}
            onBlur={() => handleInputBlur(p)}
            type="text"
        />
    );

    const AlgorithmCard = () => (
        <Paper p="md" withBorder>
            <Title order={4}>Алгоритм (сжатое описание)</Title>
            <Divider my="sm" />
            <Text size="sm">- Источники: Jupiter (маршруты и programId), DexScreener (окна m5/1h), Birdeye (holders).</Text>
            <List spacing="xs" size="sm" withPadding>
                <List.Item>
                    Initial: каждые <Code>POLLING_INTERVAL_INITIAL</Code> сек агрегируем по whitelisted пулам (через Jupiter/DEX map):
                    ликвидность (USD) и сделки за 1ч. Если <Code>MIN_LIQUIDITY_USD</Code> и <Code>MIN_TX_COUNT</Code> выполнены — статус Active.
                </List.Item>
                <List.Item>
                    Active: каждые <Code>POLLING_INTERVAL_ACTIVE</Code> сек считаем компоненты скора по окнам 5m/1h:
                    Tx_Accel, Vol_Momentum, Holder_Growth, Orderflow_Imbalance.
                    Веса: <Code>W_tx</Code>, <Code>W_vol</Code>, <Code>W_hld</Code>, <Code>W_oi</Code>. Сглаживание: <Code>EWMA_ALPHA</Code>.
                </List.Item>
                <List.Item>
                    Даунгрейд Active→Initial: если сглаженный скор ниже <Code>MIN_SCORE_THRESHOLD</Code> дольше <Code>MIN_SCORE_DURATION_HOURS</Code> часов.
                </List.Item>
                <List.Item>
                    Archived: опрос согласно <Code>POLLING_INTERVAL_ARCHIVED</Code> (0 — выключено).
                </List.Item>
            </List>
            {config && (
                <>
                    <Divider my="sm" />
                    <Title order={5}>Whitelisting (read-only)</Title>
                    <Text size="sm">Программы (разрешённые):</Text>
                    <Group gap="xs" mt={4}>
                        {config.allowed_programs.map(pid => (
                            <Badge key={pid} variant="outline" size="sm">{pid}</Badge>
                        ))}
                    </Group>
                    <Text size="sm" mt="xs">Карта DEX → Programs:</Text>
                    <Stack gap={4}>
                        {Object.entries(config.dex_program_map).map(([dex, arr]) => (
                            <Text size="xs" key={dex}><Code>{dex}</Code>: {arr.join(', ')}</Text>
                        ))}
                    </Stack>
                    <Text size="sm" mt="sm">Кэширование:</Text>
                    <Text size="xs">Jupiter programs TTL: {config.cache_ttl.jupiter_programs_seconds}s; DexScreener pairs TTL: {config.cache_ttl.dexscreener_pairs_seconds}s</Text>
                </>
            )}
        </Paper>
    );

    return (
        <Stack>
            <Title order={2}>Настройки алгоритма</Title>
            <Text size="sm" c="dimmed">Score = W_tx·Tx_Accel + W_vol·Vol_Momentum + W_hld·Holder_Growth + W_oi·Orderflow_Imbalance; сглаживание EWMA(α = EWMA_ALPHA).</Text>

            <AlgorithmCard />

            <Divider my="md" label="General" labelPosition="center" />
            <Paper p="md" withBorder>
                <Stack>
                    {generalParams.map(p => <ParamField key={p.id} p={p} />)}
                </Stack>
            </Paper>

            <Divider my="md" label="Initial" labelPosition="center" />
            <Paper p="md" withBorder>
                <Stack>
                    {initialParams.map(p => <ParamField key={p.id} p={p} />)}
                </Stack>
            </Paper>

            <Divider my="md" label="Active" labelPosition="center" />
            <Paper p="md" withBorder>
                <Stack>
                    {activeParams.map(p => <ParamField key={p.id} p={p} />)}
                </Stack>
            </Paper>

            <Divider my="md" label="Archived" labelPosition="center" />
            <Paper p="md" withBorder>
                <Stack>
                    {archivedParams.map(p => <ParamField key={p.id} p={p} />)}
                </Stack>
            </Paper>

            <Group mt="md">
                <Button onClick={handleSubmit} loading={isLoading}>
                    Сохранить параметры
                </Button>
            </Group>
        </Stack>
    );
}
