import { useState, useEffect } from 'react'
import {
    Card, Text, Badge, Button,
    Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell,
    TextInput,
} from '@tremor/react'
import { api } from '../api/client'
import type { DistributorResponse } from '../api/api'
import Modal from '../components/Modal'

type ModalState =
    | { type: 'none' }
    | { type: 'create' }
    | { type: 'edit'; d: DistributorResponse }
    | { type: 'showKey'; username: string; key: string }
    | { type: 'delete'; d: DistributorResponse }
    | { type: 'newKey'; d: DistributorResponse }

function minPrice(d: DistributorResponse): string {
    const prices = d.daily_prices ?? []
    if (!prices.length) return '—'
    return `${Math.min(...prices.map(p => p.base_price)).toFixed(2)} PLN/kg`
}

function avgAvail(d: DistributorResponse): string {
    const prices = d.daily_prices ?? []
    if (!prices.length) return '—'
    const avg = prices.reduce((s, p) => s + p.availability_kg, 0) / prices.length
    return `${avg.toFixed(0)} kg`
}

function leadTimes(d: DistributorResponse): string {
    const params = d.delivery_params ?? []
    if (!params.length) return '—'
    const times = params.map(p => p.lead_time_days)
    const min = Math.min(...times)
    const max = Math.max(...times)
    return min === max ? `${min}d` : `${min}–${max}d`
}

function leadColor(d: DistributorResponse): 'green' | 'yellow' | 'red' {
    const params = d.delivery_params ?? []
    if (!params.length) return 'yellow'
    const max = Math.max(...params.map(p => p.lead_time_days))
    return max <= 1 ? 'green' : max <= 2 ? 'yellow' : 'red'
}

export default function Distributors() {
    const [distributors, setDistributors] = useState<DistributorResponse[]>([])
    const [loading, setLoading] = useState(true)
    const [modal, setModal] = useState<ModalState>({ type: 'none' })
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState('')
    const [copied, setCopied] = useState(false)

    const [fUsername, setFUsername] = useState('')
    const [fEmail, setFEmail] = useState('')
    const [fPhone, setFPhone] = useState('')

    const load = () => {
        api.distributors.listDistributors()
            .then(r => setDistributors(r.data))
            .catch(console.error)
            .finally(() => setLoading(false))
    }

    useEffect(() => { load() }, [])

    function openCreate() {
        setFUsername(''); setFEmail(''); setFPhone('')
        setError('')
        setModal({ type: 'create' })
    }

    function openEdit(d: DistributorResponse) {
        setFUsername(d.username ?? '')
        setFEmail(d.contact_email ?? '')
        setFPhone(d.contact_phone ?? '')
        setError('')
        setModal({ type: 'edit', d })
    }

    function close() { setModal({ type: 'none' }); setError(''); setCopied(false) }

    async function handleCreate() {
        setSaving(true); setError('')
        try {
            const distRes = await api.distributors.createDistributor({
                username: fUsername,
                contact_email: fEmail,
                contact_phone: fPhone,
                daily_prices: [],
                delivery_params: [],
            })
            const keyRes = await api.distributors.createApiKey(distRes.data.id!, {
                label: 'initial',
            })
            load()
            setModal({ type: 'showKey', username: fUsername, key: keyRes.data.key ?? '' })
        } catch (e: any) {
            setError(e?.response?.data?.detail ?? 'Create failed')
        } finally { setSaving(false) }
    }

    async function handleEdit() {
        if (modal.type !== 'edit') return
        setSaving(true); setError('')
        try {
            await api.distributors.updateDistributor(modal.d.id!, {
                username: fUsername,
                contact_email: fEmail,
                contact_phone: fPhone,
            })
            load(); close()
        } catch (e: any) {
            setError(e?.response?.data?.detail ?? 'Save failed')
        } finally { setSaving(false) }
    }

    async function handleNewKey() {
        if (modal.type !== 'newKey') return
        setSaving(true); setError('')
        try {
            const keyRes = await api.distributors.createApiKey(modal.d.id!, { label: 'regenerated' })
            setModal({ type: 'showKey', username: modal.d.username ?? '', key: keyRes.data.key ?? '' })
        } catch (e: any) {
            setError(e?.response?.data?.detail ?? 'Failed to generate key')
        } finally { setSaving(false) }
    }

    async function handleDelete() {
        if (modal.type !== 'delete') return
        setSaving(true)
        try {
            await api.distributors.deleteDistributor(modal.d.id!)
            load(); close()
        } catch (e: any) {
            setError(e?.response?.data?.detail ?? 'Delete failed')
        } finally { setSaving(false) }
    }

    function copyKey(key: string) {
        navigator.clipboard.writeText(key)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const canSave = fUsername.trim() && fEmail.trim() && fPhone.trim()

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-xl font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
                        Distributors
                    </h1>
                    <p className="text-sm text-tremor-content-subtle dark:text-dark-tremor-content-subtle mt-0.5">
                        Manage coffee suppliers
                    </p>
                </div>
                <Button size="sm" onClick={openCreate}>Add distributor</Button>
            </div>

            <Card>
                {loading ? (
                    <Text>Loading…</Text>
                ) : distributors.length === 0 ? (
                    <Text className="text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                        No distributors yet. Add one to get started.
                    </Text>
                ) : (
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableHeaderCell>Distributor</TableHeaderCell>
                                <TableHeaderCell>Contact</TableHeaderCell>
                                <TableHeaderCell>Min price</TableHeaderCell>
                                <TableHeaderCell>Avg availability</TableHeaderCell>
                                <TableHeaderCell>Lead time</TableHeaderCell>
                                <TableHeaderCell>Status</TableHeaderCell>
                                <TableHeaderCell>Actions</TableHeaderCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {distributors.map(d => (
                                <TableRow key={d.id}>
                                    <TableCell>
                                        <Text className="font-medium">{d.username}</Text>
                                        <Text className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                                            {d.contact_email}
                                        </Text>
                                    </TableCell>
                                    <TableCell>
                                        <Text className="text-sm">{d.contact_phone}</Text>
                                    </TableCell>
                                    <TableCell>
                                        <Text className="font-medium">{minPrice(d)}</Text>
                                    </TableCell>
                                    <TableCell>
                                        <Text>{avgAvail(d)}</Text>
                                    </TableCell>
                                    <TableCell>
                                        <Badge color={leadColor(d)}>{leadTimes(d)}</Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge color={d.active ? 'green' : 'gray'}>{d.active ? 'Active' : 'Inactive'}</Badge>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex gap-2">
                                            <Button size="xs" variant="secondary" onClick={() => openEdit(d)}>Edit</Button>
                                            <Button size="xs" variant="secondary" onClick={() => { setError(''); setModal({ type: 'newKey', d }) }}>
                                                New key
                                            </Button>
                                            <Button size="xs" variant="secondary" color="red" onClick={() => setModal({ type: 'delete', d })}>
                                                Remove
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </Card>

            {modal.type === 'create' && (
                <Modal title="Add distributor" onClose={close} maxWidth="max-w-sm">
                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">Username *</label>
                            <TextInput value={fUsername} onChange={e => setFUsername(e.target.value)} />
                        </div>
                        <div>
                            <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">Email *</label>
                            <TextInput
                                type="email"
                                value={fEmail}
                                onChange={e => setFEmail(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">Phone *</label>
                            <TextInput value={fPhone} onChange={e => setFPhone(e.target.value)} />
                        </div>
                        <p className="text-xs text-tremor-content-subtle dark:text-dark-tremor-content-subtle">
                            An API key will be generated. Share it with the distributor so they can log in and configure their prices.
                        </p>
                        {error && <p className="text-sm text-red-500">{error}</p>}
                        <div className="flex gap-2 pt-2 border-t border-tremor-border dark:border-dark-tremor-border">
                            <Button onClick={handleCreate} loading={saving} disabled={!canSave}>
                                Create &amp; generate key
                            </Button>
                            <Button variant="secondary" onClick={close}>Cancel</Button>
                        </div>
                    </div>
                </Modal>
            )}

            {modal.type === 'showKey' && (
                <Modal title="API key generated" onClose={close} maxWidth="max-w-sm">
                    <div className="space-y-4">
                        <p className="text-sm text-tremor-content dark:text-dark-tremor-content">
                            New API key for <strong>{modal.username}</strong>. Share it with the distributor — it won't be shown again.
                        </p>
                        <div className="rounded-tremor-default bg-tremor-background-muted dark:bg-dark-tremor-background-muted p-3">
                            <p className="font-mono text-sm text-tremor-content-strong dark:text-dark-tremor-content-strong break-all">
                                {modal.key}
                            </p>
                        </div>
                        <Button onClick={() => copyKey(modal.key)} variant="secondary" className="w-full">
                            {copied ? 'Copied!' : 'Copy key'}
                        </Button>
                        <div className="pt-2 border-t border-tremor-border dark:border-dark-tremor-border">
                            <Button onClick={close} className="w-full">Done</Button>
                        </div>
                    </div>
                </Modal>
            )}

            {modal.type === 'edit' && (
                <Modal title={`Edit: ${modal.d.username}`} onClose={close} maxWidth="max-w-sm">
                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">Username *</label>
                            <TextInput value={fUsername} onChange={e => setFUsername(e.target.value)} />
                        </div>
                        <div>
                            <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">Email *</label>
                            <TextInput type="email" value={fEmail} onChange={e => setFEmail(e.target.value)} />
                        </div>
                        <div>
                            <label className="block text-xs text-tremor-content dark:text-dark-tremor-content mb-1">Phone *</label>
                            <TextInput value={fPhone} onChange={e => setFPhone(e.target.value)} />
                        </div>
                        {error && <p className="text-sm text-red-500">{error}</p>}
                        <div className="flex gap-2 pt-2 border-t border-tremor-border dark:border-dark-tremor-border">
                            <Button onClick={handleEdit} loading={saving} disabled={!canSave}>Save changes</Button>
                            <Button variant="secondary" onClick={close}>Cancel</Button>
                        </div>
                    </div>
                </Modal>
            )}

            {modal.type === 'delete' && (
                <Modal title="Remove distributor" onClose={close} maxWidth="max-w-sm">
                    <p className="text-sm text-tremor-content dark:text-dark-tremor-content mb-4">
                        Are you sure you want to remove <strong>{modal.d.username}</strong>? This cannot be undone.
                    </p>
                    {error && <p className="text-sm text-red-500 mb-3">{error}</p>}
                    <div className="flex gap-2">
                        <Button color="red" onClick={handleDelete} loading={saving}>Remove</Button>
                        <Button variant="secondary" onClick={close}>Cancel</Button>
                    </div>
                </Modal>
            )}

            {modal.type === 'newKey' && (
                <Modal title="Generate new API key" onClose={close} maxWidth="max-w-sm">
                    <p className="text-sm text-tremor-content dark:text-dark-tremor-content mb-4">
                        Generate a new API key for <strong>{modal.d.username}</strong>? Their existing keys will remain active — revoke them manually if needed.
                    </p>
                    {error && <p className="text-sm text-red-500 mb-3">{error}</p>}
                    <div className="flex gap-2">
                        <Button onClick={handleNewKey} loading={saving}>Generate key</Button>
                        <Button variant="secondary" onClick={close}>Cancel</Button>
                    </div>
                </Modal>
            )}
        </div>
    )
}
