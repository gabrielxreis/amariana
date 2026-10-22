"""Mariana: dossier from the user's AIs, LinkedIn kit, lead sheet, remake samples."""

import json

import pytest

from harvey import dossie, ficha, linkedin_kit, portfolio, samples
from harvey.models.company import Company
from harvey.models.prospect import Prospect
from tests.test_mariana_closing import FakeBrain, _config, _db


def test_merge_replaces_same_source(tmp_path):
    path = tmp_path / "sobre.md"
    dossie.merge("ChatGPT", "primeira versão", path)
    dossie.merge("Claude", "memória", path)
    dossie.merge("ChatGPT", "segunda versão", path)
    text = path.read_text()
    assert text.count("## Fonte: ChatGPT") == 1
    assert "segunda versão" in text and "primeira versão" not in text
    assert "memória" in text


def test_read_claude_memory_strips_frontmatter(tmp_path):
    (tmp_path / "MEMORY.md").write_text("- [x](x.md)")
    (tmp_path / "x.md").write_text("---\nname: x\ndescription: Filmmaker no Rio\n---\n\nFaz reels.\n")
    (tmp_path / "f.md").write_text("---\nname: f\ndescription: regra\nmetadata:\n  type: feedback\n---\nNunca X.\n")
    text = dossie.read_claude_memory(tmp_path)
    assert "### Filmmaker no Rio" in text and "Faz reels." in text
    assert "Nunca X." not in text
    assert "name: x" not in text


def test_gaps_counts_unknowns():
    assert dossie.gaps("Cidade: NÃO SEI\nIdade: nao sei") == 2


def test_prompt_has_tastes_and_doors():
    text = dossie.prompt_text()
    assert "Gostos" in text and "abrem portas" in text and "—" not in text


@pytest.mark.asyncio
async def test_profile_is_rendered_without_dashes(tmp_path, monkeypatch):
    knowledge = tmp_path / "pk.md"
    knowledge.write_text("Ana, filmmaker de igrejas no Rio.")
    monkeypatch.setattr(linkedin_kit, "KNOWLEDGE_FILE", knowledge)
    monkeypatch.setattr(linkedin_kit, "SOBRE_FILE", tmp_path / "nada.md")
    monkeypatch.setattr(linkedin_kit, "OUT_DIR", tmp_path / "li")
    monkeypatch.setattr(portfolio, "load_items", lambda *a, **k: [])
    brain = FakeBrain(json_result={
        "headlines": [{"pt": "Filmmaker — igrejas", "en": "Filmmaker for churches", "why": "busca"}],
        "about": {"pt": "Sobre PT", "en": "About EN"},
        "experience": [{"title": "Filmmaker", "company": "Lima Filmes", "period": "2020",
                        "location": "Rio", "description": {"pt": "fiz", "en": "did"}}],
        "skills": ["Edição", "DaVinci"], "custom_url": "analima", "missing": ["foto"],
    })
    path = await linkedin_kit.build_profile(brain)
    text = path.read_text()
    assert "Filmmaker , igrejas" in text and "—" not in text
    assert "About EN" in text and "linkedin.com/in/analima" in text and "- foto" in text
    assert json.loads((tmp_path / "li" / "perfil.json").read_text())["custom_url"] == "analima"


@pytest.mark.asyncio
async def test_profile_needs_material(tmp_path, monkeypatch):
    monkeypatch.setattr(linkedin_kit, "KNOWLEDGE_FILE", tmp_path / "a.md")
    monkeypatch.setattr(linkedin_kit, "SOBRE_FILE", tmp_path / "b.md")
    with pytest.raises(ValueError):
        await linkedin_kit.build_profile(FakeBrain())


async def _linkedin_items(sm, n):
    ids = []
    for i in range(n):
        ids.append(await sm.add_channel_item(
            channel="linkedin", target=f"https://www.linkedin.com/in/p{i}", body=f"Oi {i}",
            prospect_id=f"p{i}", campaign_id=f"c{i}"))
    return ids


@pytest.mark.asyncio
async def test_queue_respects_daily_cap_and_marks_sent(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    await _linkedin_items(sm, 4)
    assert await linkedin_kit.approve_pending(sm) == 4
    monkeypatch.setattr(linkedin_kit.webbrowser, "open", lambda url: None)
    monkeypatch.setattr(linkedin_kit, "copy_to_clipboard", lambda t: True)
    config = _config(channels={"email": {"provider": "smtp"},
                               "linkedin": {"max_daily_messages": 2}})
    answers = iter(["", "p"])
    sent = await linkedin_kit.queue(sm, config, ask=lambda _: next(answers), out=lambda *a: None)
    assert sent == 1
    assert await sm.count_channel_sent_today("linkedin") == 1
    assert len(await sm.get_channel_items("linkedin", "approved")) == 3


@pytest.mark.asyncio
async def test_ficha_writes_sheet_and_feeds_notes(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    cid = await sm.add_company(Company(name="Igreja Vida", domain="vida.org", industry="igreja"))
    pid = await sm.add_prospect(Prospect(company_id=cid, first_name="Bia", last_name="Souza",
                                         title="Pastora", company="Igreja Vida",
                                         personalization_notes="culto jovem às sextas"))
    monkeypatch.setattr(ficha, "OUT_DIR", tmp_path / "fichas")
    monkeypatch.setattr(ficha, "KNOWLEDGE_FILE", tmp_path / "x.md")
    monkeypatch.setattr(ficha, "SOBRE_FILE", tmp_path / "y.md")
    monkeypatch.setattr(portfolio, "load_items", lambda *a, **k: [])
    brain = FakeBrain(json_result={
        "summary": "Igreja com culto jovem forte.",
        "interests": [{"what": "louvor", "evidence": "site, página Ministérios"}],
        "icebreakers": ["Vi o culto jovem de sexta — muito vivo"],
        "works": [{"title": "Reel Conferência", "url": "https://vimeo.com/1", "why": "mesmo público"}],
    })
    path = await ficha.build(sm, brain, pid, crawl=False)
    text = path.read_text()
    assert "louvor" in text and "Reel Conferência" in text and "—" not in text
    notes = (await sm.get_prospect(pid)).personalization_notes
    assert notes.startswith("culto jovem às sextas") and ficha.NOTE_TAG in notes
    await ficha.build(sm, brain, pid, crawl=False)
    assert (await sm.get_prospect(pid)).personalization_notes.count(ficha.NOTE_TAG) == 1


@pytest.mark.asyncio
async def test_remake_brief_and_folder(tmp_path, monkeypatch):
    sm = await _db(tmp_path)
    cid = await sm.add_company(Company(name="Studio Fit", domain="fit.com", industry="academia"))
    pid = await sm.add_prospect(Prospect(company_id=cid, first_name="Leo", last_name="Reis",
                                         title="Dono", company="Studio Fit", score=90,
                                         status="contacted"))
    from harvey.signals import seed_signal_catalog
    await seed_signal_catalog(sm)
    await sm.add_observation("INSTAGRAM_PROFILE", company_id=cid, collector="test",
                             value_text="https://instagram.com/studiofit")
    monkeypatch.setattr(samples, "OUT_DIR", tmp_path / "amostras")
    import harvey.production as production
    monkeypatch.setattr(production, "clients_dir", lambda config=None: tmp_path / "clientes")
    path, leads = await samples.write_briefs(sm, top=3, mode="remake", config=_config())
    text = open(path).read()
    assert path.endswith("-remake.md") and "antes e depois" in text and "--modo remake" in text
    folder = tmp_path / "clientes" / "Studio Fit (amostra)"
    assert leads[0]["folder"] == str(folder)
    assert "instagram.com/studiofit" in (folder / "briefing-amostra.md").read_text()
    assert pid
