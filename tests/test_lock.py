from wadesk import lock


def test_hash_and_verify_round_trip():
    stored = lock.hash_pin("2468")
    algo, iterations, salt, digest = stored.split("$")
    assert algo == "pbkdf2_sha256"
    assert int(iterations) == lock.ITERATIONS
    assert len(bytes.fromhex(salt)) == 16
    assert len(bytes.fromhex(digest)) == 32
    assert lock.verify_pin("2468", stored)
    assert not lock.verify_pin("2469", stored)


def test_same_pin_gets_a_new_salt_each_time():
    assert lock.hash_pin("1234") != lock.hash_pin("1234")


def test_verify_rejects_malformed_or_foreign_hashes():
    good = lock.hash_pin("1234")
    for stored in ("", "1234", "md5$1$00$00", good.replace("pbkdf2_sha256", "sha1"),
                   "pbkdf2_sha256$x$00$00", "pbkdf2_sha256$1000$zz$00"):
        assert not lock.verify_pin("1234", stored)


def test_unicode_pin():
    stored = lock.hash_pin("kunci-ü")
    assert lock.verify_pin("kunci-ü", stored)
    assert not lock.verify_pin("kunci-u", stored)


def test_check_new_pin():
    assert lock.check_new_pin("123", "123") is not None
    assert lock.check_new_pin("1" * 33, "1" * 33) is not None
    assert lock.check_new_pin("1234", "1235") == "The PINs do not match."
    assert lock.check_new_pin("1234", "1234") is None
    assert lock.check_new_pin("a" * 32, "a" * 32) is None


def test_lockout_grows_and_is_capped():
    free = lock.FREE_ATTEMPTS
    assert [lock.lockout_seconds(n) for n in range(free)] == [0] * free
    assert lock.lockout_seconds(free) == 30
    assert lock.lockout_seconds(free + 1) == 60
    assert lock.lockout_seconds(free + 2) == 120
    assert lock.lockout_seconds(free + 20) == 600
