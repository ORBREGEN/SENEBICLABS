import { redirect } from 'next/navigation'

// The eval business is now the homepage. Keep /evaluate working for any old
// links or bookmarks by sending them to the root.
export default function EvaluateRedirect() {
  redirect('/')
}
