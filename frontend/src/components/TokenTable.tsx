import { useEffect, useState } from 'react';
import { Table, ScrollArea, Text, Tabs, Badge, rem, Group, Anchor } from '@mantine/core';
import { useInterval } from '@mantine/hooks';
import { fetchTokens } from '../services/api';
import type { Token } from '../services/api';

export function TokenTable() {
    const [tokens, setTokens] = useState<Token[]>([]);
    const [activeTab, setActiveTab] = useState<string | null>('All');

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

    // Calculate counts for each status
    const statusCounts = tokens.reduce((acc, token) => {
        acc[token.status] = (acc[token.status] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const initialCount = statusCounts['Initial'] || 0;
    const activeCount = statusCounts['Active'] || 0;
    const archivedCount = statusCounts['Archived'] || 0;

    // Filter tokens based on the active tab
    const filteredTokens = tokens.filter(token => {
        if (activeTab === 'All') return true;
        return token.status === activeTab;
    });

    const rows = filteredTokens.map((token) => (
        <Table.Tr key={token.id}>
            <Table.Td>{token.name || 'N/A'}</Table.Td>
            <Table.Td><code>{token.token_address}</code></Table.Td>
            <Table.Td>{token.status}</Table.Td>
            <Table.Td>{token.last_smoothed_score?.toFixed(4) ?? 'N/A'}</Table.Td>
            <Table.Td>
                <Group gap="xs">
                    {token.pools.map(pool => (
                        <Anchor href={`https://solscan.io/account/${pool.pool_address}`} target="_blank" key={pool.id}>
                            <Badge variant="outline">{pool.dex_name}</Badge>
                        </Anchor>
                    ))}
                </Group>
            </Table.Td>
        </Table.Tr>
    ));

    const badgeStyle = { marginLeft: rem(8) };

    return (
        <Tabs value={activeTab} onChange={setActiveTab}>
            <Tabs.List>
                <Tabs.Tab value="All">
                    All <Badge circle style={badgeStyle}>{tokens.length}</Badge>
                </Tabs.Tab>
                <Tabs.Tab value="Active" color="green">
                    Active <Badge circle color="green" style={badgeStyle}>{activeCount}</Badge>
                </Tabs.Tab>
                <Tabs.Tab value="Initial" color="yellow">
                    Initial <Badge circle color="yellow" style={badgeStyle}>{initialCount}</Badge>
                </Tabs.Tab>
                <Tabs.Tab value="Archived" color="gray">
                    Archived <Badge circle color="gray" style={badgeStyle}>{archivedCount}</Badge>
                </Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value={activeTab ?? 'All'} pt="xs">
                <ScrollArea>
                    <Table miw={1200} verticalSpacing="sm">
                        <Table.Thead>
                            <Table.Tr>
                                <Table.Th>Token Name</Table.Th>
                                <Table.Th>Token Address</Table.Th>
                                <Table.Th>Status</Table.Th>
                                <Table.Th>Score</Table.Th>
                                <Table.Th>DEXs</Table.Th>
                            </Table.Tr>
                        </Table.Thead>
                        <Table.Tbody>
                            {rows.length > 0 ? (
                                rows
                            ) : (
                                <Table.Tr>
                                    <Table.Td colSpan={5}>
                                        <Text c="dimmed" ta="center">
                                            No tokens found for this status.
                                        </Text>
                                    </Table.Td>
                                </Table.Tr>
                            )}
                        </Table.Tbody>
                    </Table>
                </ScrollArea>
            </Tabs.Panel>
        </Tabs>
    );
}
