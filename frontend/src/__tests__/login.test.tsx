import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../stores/AuthContext'
import LoginPage from '../pages/LoginPage'

function renderLogin() {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('LoginPage', () => {
  it('タイトルとログインフォームを表示する', async () => {
    renderLogin()
    expect(await screen.findByAltText('一般社団法人 Be.カラフル')).toBeInTheDocument()
    expect(screen.getByText('メールアドレス')).toBeInTheDocument()
    expect(screen.getByText('パスワード')).toBeInTheDocument()
  })

  it('未入力で送信すると日本語の検証エラーを表示する', async () => {
    const user = userEvent.setup()
    renderLogin()
    await user.click(await screen.findByRole('button', { name: 'ログイン' }))
    expect(await screen.findByText('メールアドレスを入力してください')).toBeInTheDocument()
    expect(screen.getByText('パスワードを入力してください')).toBeInTheDocument()
  })

  it('医療診断ではない旨の注意書きを表示する', async () => {
    renderLogin()
    expect(await screen.findByText(/医療診断ではなく/)).toBeInTheDocument()
  })

  it('「次回から入力を省略する」チェックボックスを表示する（初期は未チェック）', async () => {
    localStorage.clear()
    renderLogin()
    const checkbox = await screen.findByRole('checkbox', { name: /次回から入力を省略する/ })
    expect(checkbox).not.toBeChecked()
  })

  it('保存済みのログイン情報があれば入力欄へ自動入力される', async () => {
    localStorage.setItem(
      'becolorful_saved_login',
      JSON.stringify({ email: 'saved@example.com', password: 'Secret123!' }),
    )
    renderLogin()
    const checkbox = await screen.findByRole('checkbox', { name: /次回から入力を省略する/ })
    expect(checkbox).toBeChecked()
    expect(screen.getByDisplayValue('saved@example.com')).toBeInTheDocument()
    localStorage.clear()
  })
})
