import React from 'react'
import {
  Button,
  Card,
  Checkbox,
  Input,
  Pill,
  Radio,
  Select,
  Skeleton,
  Spinner,
  Textarea,
  Toast,
} from './index'

export default {
  title: 'UI/Atoms',
}

export const CoreStates = () => (
  <div className="grid gap-4 bg-bg p-6 text-fg">
    <Card className="grid gap-3">
      <div className="flex flex-wrap gap-2">
        <Button variant="primary">Primary</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="danger">Danger</Button>
        <Button loading>Signing you in...</Button>
      </div>
      <Input label="Email" placeholder="researcher@iitgn.ac.in" />
      <Textarea label="Question" placeholder="Ask about Indian research..." />
      <Select label="Tier">
        <option>Researcher</option>
        <option>Government</option>
        <option>Industry</option>
      </Select>
      <label className="flex items-center gap-2 text-sm"><Checkbox /> Checkbox</label>
      <label className="flex items-center gap-2 text-sm"><Radio name="atom-radio" /> Radio</label>
      <div className="flex gap-2">
        <Pill tone="success">high confidence</Pill>
        <Pill tone="warning">medium confidence</Pill>
        <Pill>Tier 1</Pill>
      </div>
      <Skeleton className="h-12" />
      <Toast tone="info">Audit chain live</Toast>
      <Spinner label="Checking evidence" />
    </Card>
  </div>
)
