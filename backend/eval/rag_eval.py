"""RAG değerlendirme (eval) betiği.

NEDEN EVAL?
    "Daha iyi oldu galiba" ile RAG ayarlanmaz. Gerçekçi sorulardan oluşan sabit bir soru seti
    (questions.json) ve her soru için "doğru cevabın bulunduğu kayıt(lar)" ile aramayı ÖLÇERİZ. Chunk
    boyutunu, normalizasyonu, eşiği değiştirince sayıların nasıl oynadığına bakarak karar veririz.

METRİKLER (cevabı olan sorular için)
    Recall@1 : doğru kayıt ilk sonuçta mı?
    Recall@5 : doğru kayıt ilk 5 sonuçta mı?        <- hedefimiz >= 0.90
    MRR      : doğru kaydın sırasının tersinin ortalaması (1. sırada=1.0, 2.=0.5, 3.=0.33 ...)
    "Doğru" = sonuçtaki kayıt başlığı, sorunun `expected` listesindeki başlıklardan biri.

CEVABI OLMAYAN SORULAR (no_answer=true)
    Bunlarda beklenen: below_threshold=True (bot "bilmiyorum" demeli). Ayrıca cevabı OLAN soruların kaçının
    yanlışlıkla eşik altı sayıldığını (false reject) raporlarız. Eşik ayarı bu ikisi arasındaki dengedir.

ÇALIŞTIRMA (backend/ klasöründen):
    .venv/Scripts/python.exe -m eval.rag_eval            # özet + hatalar
    .venv/Scripts/python.exe -m eval.rag_eval -v         # her soru için ayrıntı
Sunucunun indeksi oluşturmuş olması gerekir (bungai.db içinde parçalar). Embedding için API anahtarı gerekir.
"""
import json
import sys
from functools import lru_cache
from pathlib import Path

from app.database import SessionLocal
import importlib

search_mod = importlib.import_module("app.rag.search")  # (app.rag.search adı pakette fonksiyonla gölgelendiği için)

QUESTIONS = json.loads((Path(__file__).parent / "questions.json").read_text(encoding="utf-8"))
TOP_K = 5

# Aynı sorgunun embedding'ini üç yöntem için tekrar tekrar API'den almayalım.
_orig_embed = search_mod.embed_query
search_mod.embed_query = lru_cache(maxsize=None)(_orig_embed)


def run(method: str, apply_threshold: bool):
    """Tüm sorular için arama yapar. Eşik kapalıysa sıralama kalitesi (eşikten bağımsız) ölçülür."""
    saved = (search_mod.VECTOR_MIN_COSINE, search_mod.KEYWORD_MIN_SCORE)
    if not apply_threshold:
        search_mod.VECTOR_MIN_COSINE, search_mod.KEYWORD_MIN_SCORE = -1.0, -1.0
    try:
        with SessionLocal() as db:
            return [search_mod.search(db, item["q"], top_k=TOP_K, method=method) for item in QUESTIONS]
    finally:
        search_mod.VECTOR_MIN_COSINE, search_mod.KEYWORD_MIN_SCORE = saved


def first_correct_rank(trace, expected: list[str]) -> int | None:
    for rank, hit in enumerate(trace.results, start=1):
        if hit.entry_title in expected:
            return rank
    return None


def ranking_metrics(method: str):
    traces = run(method, apply_threshold=False)
    ranks, misses = [], []
    for item, trace in zip(QUESTIONS, traces):
        if item.get("no_answer"):
            continue
        r = first_correct_rank(trace, item["expected"])
        ranks.append(r)
        if r is None or r > 5:
            misses.append((item, trace))
    n = len(ranks)
    r1 = sum(1 for r in ranks if r == 1) / n
    r5 = sum(1 for r in ranks if r is not None and r <= 5) / n
    mrr = sum(1 / r for r in ranks if r) / n
    return {"n": n, "recall1": r1, "recall5": r5, "mrr": mrr}, misses, traces


def threshold_report(verbose: bool):
    """Gerçek eşiklerle hibrit arama: cevapsızlarda below_threshold doğruluğu + yanlış red oranı."""
    traces = run("hybrid", apply_threshold=True)
    no_ans = [(i, t) for i, t in zip(QUESTIONS, traces) if i.get("no_answer")]
    ans = [(i, t) for i, t in zip(QUESTIONS, traces) if not i.get("no_answer")]
    correct = sum(1 for _, t in no_ans if t.below_threshold)
    false_reject = [(i, t) for i, t in ans if t.below_threshold]
    print(f"\nEŞİK (VECTOR_MIN_COSINE={search_mod.VECTOR_MIN_COSINE}, KEYWORD_MIN_SCORE={search_mod.KEYWORD_MIN_SCORE})")
    print(f"  Cevapsız sorularda doğru 'bilmiyorum': {correct}/{len(no_ans)}")
    print(f"  Cevaplı sorularda yanlış red (false reject): {len(false_reject)}/{len(ans)}")
    for i, t in no_ans:
        if not t.below_threshold:
            top = t.results[0]
            print(f"   ! cevapsız ama sonuç döndü: '{i['q']}' -> {top.entry_title} (cos={top.vector_score}, bm25={top.keyword_score})")
    for i, _ in false_reject:
        print(f"   ! yanlış red: '{i['q']}'")


def score_distribution():
    """Eşik kalibrasyonu için: cevaplı/cevapsız soruların en iyi vektör ve BM25 skorları."""
    traces = run("hybrid", apply_threshold=False)
    rows = []
    for item, trace in zip(QUESTIONS, traces):
        vec = max((h.vector_score for h in trace.results if h.vector_score is not None), default=0.0)
        kw = max((h.keyword_score for h in trace.results if h.keyword_score is not None), default=0.0)
        rows.append((item.get("no_answer", False), vec, kw, item["q"]))
    for flag in (False, True):
        sel = [r for r in rows if r[0] == flag]
        label = "CEVAPSIZ" if flag else "CEVAPLI  "
        vs, ks = sorted(r[1] for r in sel), sorted(r[2] for r in sel)
        print(f"  {label} en iyi cos: min={vs[0]:.3f} medyan={vs[len(vs)//2]:.3f} max={vs[-1]:.3f} | en iyi bm25: min={ks[0]:.2f} medyan={ks[len(ks)//2]:.2f} max={ks[-1]:.2f}")
    print("  Cevapsız soruların skorları:")
    for r in rows:
        if r[0]:
            print(f"    cos={r[1]:.3f} bm25={r[2]:.2f}  {r[3]}")


def main() -> None:
    verbose = "-v" in sys.argv
    print(f"Soru sayısı: {len(QUESTIONS)} (cevaplı: {sum(1 for q in QUESTIONS if not q.get('no_answer'))}, cevapsız: {sum(1 for q in QUESTIONS if q.get('no_answer'))})")
    print("\nSIRALAMA KALİTESİ (eşik uygulanmadan)")
    print(f"{'yöntem':<10} {'Recall@1':>9} {'Recall@5':>9} {'MRR':>7}")
    hybrid_misses = []
    for method in ("vector", "keyword", "hybrid"):
        m, misses, traces = ranking_metrics(method)
        print(f"{method:<10} {m['recall1']:>9.3f} {m['recall5']:>9.3f} {m['mrr']:>7.3f}")
        if method == "hybrid":
            hybrid_misses = misses
            if verbose:
                for item, trace in zip(QUESTIONS, traces):
                    top = [f"{h.entry_title[:28]}" for h in trace.results[:3]]
                    print(f"   {item['q'][:48]:<48} -> {top}")
    print(f"\nHİBRİT KAÇIRILANLAR (ilk 5'te doğru kayıt yok): {len(hybrid_misses)}")
    for item, trace in hybrid_misses:
        got = [h.entry_title[:30] for h in trace.results[:3]]
        print(f"  - '{item['q']}'  beklenen={item['expected'][:2]}  gelen={got}  (normalize: '{trace.normalized_query}')")
    print("\nSKOR DAĞILIMI")
    score_distribution()
    threshold_report(verbose)


if __name__ == "__main__":
    main()
