

'''
class ScanResult(collections.namedtuple('ScanResult', 'response override_url title content_type content')):




                    # a hotlinked image
                    if response.data_type == 'image' and Image is not None:

                    # html page.. extract some info
                    elif response.data_type == 'soup':
                        log.info('Content: HTML page')

                        # get title of page
                        with trapped:
                            link.title = text.decode(response.data.title.string).strip()
                            log.info('Title: %r', link.title)

                    # no idea.. just save what we got
                    else:
                        log.info('Content: Unknown (%s)', response.content_type)
                        link.content_type = response.content_type

                else:
                    log.info('Error: %d %s', response.code, response.msg)
                    publish = False
                    link.content = response.msg
                    if response.code == 404:
                        fatal = True

        except TrapError, exc:
            log.warn('Failure scanning link', exc_info=exc.args)
            link.content = exc
            publish = False

        if publish:
            link.publish(commit=False)
        else:
            link.error_count += 1
            if fatal or (max_errors is not None and link.error_count >= max_errors):
                link.state = 'invalid'
                log.info('Link is marked as permanently invalid')

        if dry_run:
            log.info('Dry run, not saving results')
        else:
            link.save()
'''
