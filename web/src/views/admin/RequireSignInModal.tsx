"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button, InputTypeIn, Modal } from "@opal/components";
import { Section, toast } from "@opal/layouts";

interface RequireSignInModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

/**
 * Turns sign-in on for a deployment running in single-user mode.
 *
 * The credentials land on the existing local account, so the operator keeps
 * their chat history. The backend refuses to flip the setting without them.
 */
export default function RequireSignInModal({
  open,
  onOpenChange,
  onSuccess,
}: RequireSignInModalProps) {
  const t = useTranslations("admin.security.authentication.requireSignIn");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function close() {
    setEmail("");
    setPassword("");
    setConfirm("");
    onOpenChange(false);
  }

  async function submit() {
    if (password !== confirm) {
      toast.error(t("mismatch"));
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch(
        "/api/admin/settings/single-user-mode/disable",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        }
      );
      if (!response.ok) {
        throw new Error((await response.json()).detail);
      }
      toast.success(t("success"));
      close();
      onSuccess();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <Modal.Content width="md" height="fit">
        <Modal.Header
          title={t("dialogTitle")}
          description={t("dialogDescription")}
          onClose={close}
        />
        <Modal.Body>
          <Section gap={1} alignItems="start">
            <InputTypeIn
              type="email"
              placeholder={t("emailLabel")}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <InputTypeIn
              type="password"
              placeholder={t("passwordLabel")}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <InputTypeIn
              type="password"
              placeholder={t("confirmLabel")}
              value={confirm}
              onChange={(event) => setConfirm(event.target.value)}
            />
          </Section>
        </Modal.Body>
        <Modal.Footer>
          <Button prominence="secondary" onClick={close}>
            {t("cancel")}
          </Button>
          <Button
            prominence="primary"
            onClick={() => void submit()}
            disabled={submitting || !email || !password || !confirm}
          >
            {t("submit")}
          </Button>
        </Modal.Footer>
      </Modal.Content>
    </Modal>
  );
}
