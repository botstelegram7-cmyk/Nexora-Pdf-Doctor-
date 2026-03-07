        )
        return True
    elif state == "resume_edu":
        text_input = (msg.text or "").strip()
        if text_input.lower() != "skip":
            ctx.user_data["resume_data"]["education"] = text_input.split("\n")
        # Generate resume now
        prog = await msg.reply_text("⏳ Building your resume...")
        try:
            result = pdf_utils.create_resume(ctx.user_data["resume_data"])
            await _send_pdf(update, result, "resume.pdf",
                            f"📋 <b>Resume ready for {_esc(ctx.user_data['resume_data'].get('name',''))}!</b>")
            await increment_usage(user_id, "resume")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try: await prog.delete()
            except: pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("resume_data", None)
        return True

    # ── CERTIFICATE ───────────────────────────────────────────────────────────
    elif state == "cert_name":
        ctx.user_data["cert_name"] = (msg.text or "").strip()
        ctx.user_data["state"] = "cert_course"
        await msg.reply_text("🏆 Enter the course/achievement name:", reply_markup=cancel_btn())
        return True
    elif state == "cert_course":
        name   = ctx.user_data.get("cert_name","")
        course = (msg.text or "").strip()
        prog = await msg.reply_text("⏳ Generating certificate...")
        try:
            result = pdf_utils.create_certificate(name, course)
            await _send_pdf(update, result, "certificate.pdf",
                            f"🏆 <b>Certificate ready for {_esc(name)}!</b>")
            await increment_usage(user_id, "certificate")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try: await prog.delete()
            except: pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("cert_name", None)
        return True

    # ── ZIP COLLECT ───────────────────────────────────────────────────────────
    elif state == "zip_collect":
        if msg.document:
            f = await msg.document.get_file()
            data = bytes(await f.download_as_bytearray())
            ctx.user_data.setdefault("zip_files", []).append((msg.document.file_name, data))
            count = len(ctx.user_data["zip_files"])
            await msg.reply_text(f"✅ File {count} added! Send more or /done", reply_markup=cancel_btn())
        elif msg.text and msg.text.strip() == "/done":
            files = ctx.user_data.get("zip_files", [])
            if not files:
                await _err(update, "No files to zip!"); return True
            prog = await msg.reply_text("⏳ Creating ZIP...")
            try:
                result = pdf_utils.create_zip(files)
                await _send_file(update, result, "archive.zip",
                                 f"📦 <b>ZIP created!</b> {len(files)} files packed")
                await increment_usage(user_id, "zip")
            except Exception as e:
                await _err(update, str(e))
            finally:
                try: await prog.delete()
                except: pass
            ctx.user_data.pop("state", None)
            ctx.user_data.pop("zip_files", None)
        return True

    # ── UNZIP ─────────────────────────────────────────────────────────────────
    elif state == "unzip":
        if not msg.document:
            await _err(update, "Send a .zip file!"); return True
        prog = await msg.reply_text("⏳ Extracting ZIP...")
        try:
            f = await msg.document.get_file()
            data = bytes(await f.download_as_bytearray())
            files = pdf_utils.extract_zip(data)
            await msg.reply_text(f"📂 Found <b>{len(files)}</b> files. Sending them now...", parse_mode="HTML")
            for fname, fdata in files[:10]:
                await update.effective_message.reply_document(
                    document=InputFile(io.BytesIO(fdata), filename=fname),
                    caption=f"📄 {_esc(fname)} ({pdf_utils.file_size_str(fdata)})",
                    parse_mode="HTML"
                )
                await asyncio.sleep(0.5)
            await increment_usage(user_id, "unzip")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try: await prog.delete()
            except: pass
        ctx.user_data.pop("state", None)
        return True

    # ── FILE INFO ─────────────────────────────────────────────────────────────
    elif state == "fileinfo":
        if not (msg.document or msg.photo):
            await _err(update, "Send any file or image!"); return True
        prog = await msg.reply_text("⏳ Analyzing file...")
        try:
            if msg.document:
                f = await msg.document.get_file()
                data = bytes(await f.download_as_bytearray())
                filename = msg.document.file_name or "file"
            else:
                f = await msg.photo[-1].get_file()
                data = bytes(await f.download_as_bytearray())
                filename = "photo.jpg"
            info = pdf_utils.get_file_info(data, filename)
            dims = f"\n  📐 Dimensions: <b>{info.get('width')}×{info.get('height')}px</b>" if "width" in info else ""
            pages_info = f"\n  📄 Pages: <b>{info.get('pages')}</b>" if "pages" in info else ""
            text = (
                f"ℹ️ <b>File Information</b>\n\n"
                f"  📄 Name: <code>{_esc(info['filename'])}</code>\n"
                f"  🏷️ Type: <b>{info['type']}</b> ({info['extension']})\n"
                f"  💾 Size: <b>{info['size']}</b> ({info['bytes']:,} bytes)\n"
                f"  🔐 MD5: <code>{info['md5']}</code>"
                f"{dims}{pages_info}"
            )
            await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())
            await increment_usage(user_id, "fileinfo")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try: await prog.delete()
            except: pass
        ctx.user_data.pop("state", None)
        return True

    # ── QR SCAN ───────────────────────────────────────────────────────────────
    elif state == "qrcode_scan":
        data = await _get_image(update)
        if not data: return True
        prog = await msg.reply_text("⏳ Scanning QR code...")
        try:
            result = pdf_utils.scan_qr_code(data)
            await update.effective_message.reply_text(
                f"📷 <b>QR Code Decoded:</b>\n\n<code>{_esc(result)}</code>",
                parse_mode="HTML", reply_markup=back_btn()
            )
            await increment_usage(user_id, "qrcode_scan")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try: await prog.delete()
            except: pass
        ctx.user_data.pop("state", None)
        return True

    # ── BARCODE ───────────────────────────────────────────────────────────────
    elif state == "barcode":
        text_input = (msg.text or "").strip()
        if not text_input:
            await _err(update, "Enter text for barcode."); return True
        prog = await msg.reply_text("⏳ Generating barcode...")
        try:
            result = pdf_utils.generate_barcode(text_input)
            await _send_file(update, result, "barcode.png",
                             f"📊 <b>Barcode generated!</b>\nData: <code>{_esc(text_input)}</code>")
            await increment_usage(user_id, "barcode")
        except Exception as e:
            await _err(update, str(e))
        finally:
            try: await prog.delete()
            except: pass
        ctx.user_data.pop("state", None)
        return True

    # ── NOTES ADD ─────────────────────────────────────────────────────────────
    elif state == "note_add":
        text_input = (msg.text or "").strip()
        if not text_input:
            await _err(update, "Enter your note."); return True
        lines = text_input.split("\n", 1)
        title   = lines[0][:50]
        content = lines[1] if len(lines) > 1 else lines[0]
        await save_note(user_id, title, content)
        await msg.reply_text(
            f"📝 <b>Note saved!</b>\n\n<b>{_esc(title)}</b>",
            parse_mode="HTML", reply_markup=back_btn()
        )
        await increment_usage(user_id, "notes")
        ctx.user_data.pop("state", None)
        return True

    return False


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK HANDLER for new feature callbacks
# ─────────────────────────────────────────────────────────────────────────────

async def handle_new_callbacks(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    q = update.callback_query
    if not q: return False
    data = q.data

    # Impose layout
    if data in ("impose_2up", "impose_4up"):
        await q.answer()
        layout = "2up" if data == "impose_2up" else "4up"
        ctx.user_data["state"] = "impose_process"
        ctx.user_data["impose_layout"] = layout
        await q.message.reply_text(
            f"📋 <b>Layout: {layout}</b>\nNow send your PDF:",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # Image filter apply
    if data.startswith("imgf_"):
        await q.answer()
        filter_name = data[5:]
        img_data = ctx.user_data.get("img_filter_data")
        if not img_data:
            await q.message.reply_text("⚠️ Session expired. Use /img_filter again.", reply_markup=back_btn())
            return True
        prog = await q.message.reply_text("⏳ Applying filter...")
        try:
            result = pdf_utils.img_apply_filter(img_data, filter_name)
            filter_label = IMAGE_FILTERS.get(filter_name, filter_name)
            import io
            from telegram import InputFile as TIF
            sent = await q.message.reply_document(
                document=TIF(io.BytesIO(result), filename=f"{filter_name}.png"),
                caption=f"🎨 <b>Filter applied: {filter_label}</b>",
                parse_mode="HTML", reply_markup=main_menu()
            )
            from utils.cache import delete_buttons_later
            asyncio.create_task(delete_buttons_later(sent, DELETE_BUTTONS_AFTER_SEC))
            await increment_usage(q.from_user.id, "img_filter")
        except Exception as e:
            await q.message.reply_text(f"❌ Error: {str(e)[:200]}", reply_markup=back_btn())
        finally:
            try: await prog.delete()
            except: pass
        ctx.user_data.pop("state", None)
        ctx.user_data.pop("img_filter_data", None)
        return True

    # Steganography
    if data == "steg_hide":
        await q.answer()
        ctx.user_data["state"] = "steg_hide_img"
        await q.message.reply_text("🙈 <b>Step 1:</b> Send the image you want to hide a message in:",
                                    parse_mode="HTML", reply_markup=cancel_btn())
        return True
    if data == "steg_reveal":
        await q.answer()
        ctx.user_data["state"] = "steg_reveal"
        await q.message.reply_text("👁️ Send the image to reveal hidden message:",
                                    parse_mode="HTML", reply_markup=cancel_btn())
        return True

    # Poster theme
    if data.startswith("poster_"):
        await q.answer()
        theme = data.replace("poster_","")
        ctx.user_data["state"] = "poster_input"
        ctx.user_data["poster_theme"] = theme
        await q.message.reply_text(
            f"🎨 <b>Theme: {theme.title()}</b>\n\nEnter your poster title:\n"
            "For title + subtitle: <code>Title | Subtitle</code>",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True

    # Notes
    if data == "note_add":
        await q.answer()
        ctx.user_data["state"] = "note_add"
        await q.message.reply_text(
            "📝 <b>Add Note</b>\n\nFirst line = title, rest = content.\nType your note:",
            parse_mode="HTML", reply_markup=cancel_btn()
        )
        return True
    if data == "note_view":
        await q.answer()
        notes = await get_notes(q.from_user.id)
        if not notes:
            await q.message.reply_text("📒 No notes yet! Use Add Note to save one.",
                                        reply_markup=back_btn())
            return True
        text = "📒 <b>Your Notes</b>\n\n"
        for i, n in enumerate(notes, 1):
            title   = _esc(n.get("title","Note")[:40])
            content = _esc(n.get("content","")[:80])
            date    = str(n.get("created_at",""))[:10]
            text += f"{i}. 📝 <b>{title}</b>\n   <i>{content}...</i>\n   🕐 {date}\n\n"
        await q.message.reply_text(text, parse_mode="HTML", reply_markup=back_btn())
        return True

    return False
