import { useEffect, useState } from 'react';
import { Table, ScrollArea, Text } from '@mantine/core';
import { useInterval } from '@mantine/hooks';
import { fetchTokens } from '../services/api';
import type { Token } from '../services/api';

export function TokenTable() {
    const [tokens, setTokens] = useState<Token[]>([]);

    const loadTokens = async () => {
        const fetchedTokens = await fetchTokens();
        setTokens(fetchedTokens);
    };

    // Load tokens on initial render
    useEffect(() => {
        loadTokens();
    }, []);

    // Refresh tokens every 10 seconds
    const interval = useInterval(loadTokens, 10000);
    useEffect(() => {
        interval.start();
        return interval.stop;
    }, [interval]);

    const rows = tokens.map((token) => (
        <Table.Tr key={token.id}>
            <Table.Td>{token.token_address}</Table.Td>
            <Table.Td>{token.status}</Table.Td>
            <Table.Td>{token.last_smoothed_score?.toFixed(4) ?? 'N/A'}</Table.Td>
        </Table.Tr>
    ));

    return (
        <ScrollArea>
            <Table miw={800} verticalSpacing="sm">
                <Table.Thead>
                    <Table.Tr>
                        <Table.Th>Token Address</Table.Th>
                        <Table.Th>Status</Table.Th>
                        <Table.Th>Score</Table.Th>
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                    {rows.length > 0 ? (
                        rows
                    ) : (
                        <Table.Tr>
                            <Table.Td colSpan={3}>
                                <Text c="dimmed" ta="center">
                                    No tokens found. Waiting for data...
                                </Text>
                            </Table.Td>
                        </Table.Tr>
                    )}
                </Table.Tbody>
            </Table>
        </ScrollArea>
    );
}
