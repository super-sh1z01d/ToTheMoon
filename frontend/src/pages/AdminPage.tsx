import { useEffect, useState } from 'react';
import { Button, Stack, TextInput, Title, Text } from '@mantine/core';
import { fetchParameters, updateParameters } from '../services/api';
import type { ScoringParameter } from '../services/api';

export function AdminPage() {
    const [params, setParams] = useState<ScoringParameter[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        fetchParameters().then(setParams);
    }, []);

    const handleParamChange = (index: number, value: string) => {
        const newParams = [...params];
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
            newParams[index].param_value = numValue;
            setParams(newParams);
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
            default: return "";
        }
    };

    return (
        <Stack>
            <Title order={2}>Параметры скоринга</Title>
            <Text size="sm" c="dimmed">Формула расчета скора: Score = (W_tx * Tx_Accel) + (W_vol * Vol_Momentum) + (W_hld * Holder_Growth) + (W_oi * Orderflow_Imbalance)</Text>
            <Text size="sm" c="dimmed">Все входные компоненты и финальный Score проходят через сглаживание EWMA.</Text>

            {params.map((param, index) => (
                <TextInput
                    key={param.param_name}
                    label={getParamDescription(param.param_name) + (param.param_name.startsWith("POLLING_INTERVAL") ? " (секунды)" : "")}
                    description={param.param_name.startsWith("POLLING_INTERVAL") && param.param_value === 0 ? "(0 означает отключено)" : ""}
                    value={param.param_value}
                    onChange={(event) => handleParamChange(index, event.currentTarget.value)}
                    type="number"
                    step={param.param_name.startsWith("POLLING_INTERVAL") ? 1 : 0.01}
                />
            ))}
            <Button onClick={handleSubmit} loading={isLoading}>
                Сохранить параметры
            </Button>
        </Stack>
    );
}
