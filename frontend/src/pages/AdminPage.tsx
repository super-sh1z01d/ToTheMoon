import { useEffect, useState } from 'react';
import { Button, Stack, TextInput, Title } from '@mantine/core';
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

    return (
        <Stack>
            <Title order={2}>Scoring Parameters</Title>
            {params.map((param, index) => (
                <TextInput
                    key={param.id}
                    label={param.param_name}
                    value={param.param_value}
                    onChange={(event) => handleParamChange(index, event.currentTarget.value)}
                    type="number"
                    step={0.01}
                />
            ))}
            <Button onClick={handleSubmit} loading={isLoading}>
                Save Parameters
            </Button>
        </Stack>
    );
}
