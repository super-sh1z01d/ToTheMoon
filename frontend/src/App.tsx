import { AppShell, Burger, Group, NavLink, Title } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { Routes, Route, Link } from 'react-router-dom';
import { TokenTable } from './components/TokenTable';
import { AdminPage } from './pages/AdminPage';

export default function App() {
  const [opened, { toggle }] = useDisclosure();

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 250, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
          <Title order={3}>ToTheMoon Сканер</Title>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <NavLink component={Link} to="/" label="Список токенов" />
        <NavLink component={Link} to="/admin" label="Панель администратора" />
      </AppShell.Navbar>

      <AppShell.Main>
        <Routes>
          <Route path="/" element={<TokenTable />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </AppShell.Main>
    </AppShell>
  );
}
